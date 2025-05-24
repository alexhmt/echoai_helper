r"""
Оригинальный код Дэвида Нг в [GlaDOS](https://github.com/dnhkng/GlaDOS) (/glados/voice_recognition.py), лицензированный по лицензии MIT.

Оригинальная работа Copyright (c) 2022 David Ng
Измененная работа Copyright (c) 2024 Yi-Ting Chiu

Этот файл включает работу, подпадающую под следующее уведомление об авторских правах и разрешении:

Лицензия MIT

Copyright (c) 2022 David Ng

Настоящим предоставляется бесплатное разрешение любому лицу, получающему копию
этого программного обеспечения и связанных с ним файлов документации («Программное обеспечение»), на неограниченное использование Программного обеспечения,
включая, помимо прочего, права на использование, копирование, изменение, объединение, публикацию, распространение, сублицензирование и/или продажу
копий Программного обеспечения, а также на разрешение лицам, которым Программное обеспечение предоставляется для этого, при соблюдении следующих условий:

Вышеуказанное уведомление об авторских правах и это уведомление о разрешении должны быть включены во все
копии или существенные части Программного обеспечения.

ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ ПРЕДОСТАВЛЯЕТСЯ «КАК ЕСТЬ», БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ, ЯВНЫХ ИЛИ
ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ, ПОМИМО ПРОЧЕГО, ГАРАНТИИ ТОВАРНОЙ ПРИГОДНОСТИ,
ПРИГОДНОСТИ ДЛЯ ОПРЕДЕЛЕННОЙ ЦЕЛИ И НЕНАРУШЕНИЯ ПРАВ. НИ В КОЕМ СЛУЧАЕ
АВТОРЫ ИЛИ ВЛАДЕЛЬЦЫ АВТОРСКИХ ПРАВ НЕ НЕСУТ ОТВЕТСТВЕННОСТИ ЗА ЛЮБЫЕ ПРЕТЕНЗИИ, УЩЕРБ ИЛИ ДРУГУЮ
ОТВЕТСТВЕННОСТЬ, БУДЬ ТО В РЕЗУЛЬТАТЕ ДЕЙСТВИЯ ДОГОВОРА, ПРАВОНАРУШЕНИЯ ИЛИ ИНЫМ ОБРАЗОМ, ВОЗНИКАЮЩИЕ ИЗ,
В СВЯЗИ С ИЛИ В РЕЗУЛЬТАТЕ ИСПОЛЬЗОВАНИЯ ПРОГРАММНОГО ОБЕСПЕЧЕНИЯ ИЛИ ДРУГИХ ДЕЙСТВИЙ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ.

Эта измененная версия также распространяется по лицензии MIT.
"""

import threading
import queue
from pathlib import Path
from typing import Callable, List

import numpy as np
import sounddevice as sd # Библиотека для работы с аудиоустройствами
from loguru import logger # Библиотека для логирования

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__)) # Текущий каталог
sys.path.append(current_dir) # Добавление текущего каталога в путь поиска модулей

import vad # Модуль для детекции голосовой активности (VAD)

# Использование pathlib для путей, независимых от ОС
VAD_MODEL_PATH = Path(current_dir + "/models/silero_vad.onnx") # Путь к модели VAD
SAMPLE_RATE = 16000  # Частота дискретизации для входного потока
VAD_SIZE = 50  # Размер семпла в миллисекундах для детекции голосовой активности (VAD)
VAD_THRESHOLD = 0.7  # Порог для детекции VAD
BUFFER_SIZE = 600  # Размер буфера в миллисекундах перед детекцией VAD
PAUSE_LIMIT = 1300  # Допустимая пауза в миллисекундах перед обработкой
WAKE_WORD = "computer"  # Слово для активации (кодовое слово)
SIMILARITY_THRESHOLD = 2  # Порог схожести для кодового слова


class VoiceRecognitionVAD:
    """Класс для распознавания голоса с использованием детекции голосовой активности (VAD)."""
    def __init__(
        self, asr_transcribe_func: Callable, wake_word: str | None = None, function: Callable = print
    ) -> None:
        """
        Инициализирует класс VoiceRecognition, настраивая необходимые модели, потоки и очереди.

        Этот класс не является потокобезопасным, поэтому его следует использовать только из одного потока. Он работает следующим образом:
        1. Аудиопоток непрерывно прослушивает входной сигнал.
        2. Аудио буферизуется до тех пор, пока не будет обнаружена голосовая активность. Это делается для того, чтобы
           захватить все предложение целиком, включая часть до обнаружения голосовой активности.
        2. Пока голосовая активность обнаружена, аудио сохраняется вместе с буферизованным аудио.
        3. Когда голосовая активность не обнаруживается в течение короткого времени (PAUSE_LIMIT), аудио
           транскрибируется. Если в это время снова обнаруживается голос, таймер сбрасывается, и
           запись продолжается.
        4. После прекращения голоса прослушивание останавливается, и аудио транскрибируется.
        5. Если установлено кодовое слово, транскрибированный текст проверяется на схожесть с кодовым словом.
        6. Функция вызывается с транскрибированным текстом в качестве аргумента.
        7. Аудиопоток сбрасывается (буферы очищаются), и прослушивание продолжается.

        Args:
            asr_transcribe_func (Callable): Функция, используемая для автоматического распознавания речи.
            wake_word (str, optional): Кодовое слово для активации. По умолчанию None.
            func (Callable, optional): Функция, вызываемая при обнаружении кодового слова. По умолчанию print.
        """

        self._setup_audio_stream() # Настройка аудиопотока
        self._setup_vad_model()    # Настройка модели VAD
        self.transcribe = asr_transcribe_func # Функция транскрибации

        # Инициализация очередей семплов и флагов состояния
        self.samples = [] # Список для хранения семплов
        self.sample_queue = queue.Queue() # Очередь для семплов из аудиопотока
        self.buffer = queue.Queue(maxsize=BUFFER_SIZE // VAD_SIZE) # Буфер для предварительной записи
        self.recording_started = False # Флаг начала записи
        self.gap_counter = 0 # Счетчик пауз
        self.wake_word = wake_word # Кодовое слово

    def _setup_audio_stream(self):
        """
        Настраивает входной аудиопоток с использованием sounddevice.
        """
        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1, # Моно-канал
            callback=self.audio_callback, # Функция обратного вызова для обработки аудиоданных
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000), # Размер блока
        )

    def _setup_vad_model(self):
        """
        Загружает модель детекции голосовой активности (VAD).
        """
        self.vad_model = vad.VAD(model_path=VAD_MODEL_PATH)
        

    def audio_callback(self, indata, frames, time, status):
        """
        Функция обратного вызова для аудиопотока, обрабатывающая входящие данные.
        """
        data = indata.copy()
        data = data.squeeze()  # Уменьшение до одного канала, если необходимо
        vad_confidence = self.vad_model.process_chunk(data) > VAD_THRESHOLD # Определение уверенности VAD
        self.sample_queue.put((data, vad_confidence)) # Помещение данных и уверенности VAD в очередь

    def start(self):
        """
        Запускает голосового ассистента, непрерывно прослушивая входной сигнал и отвечая.
        (Этот метод, похоже, предназначен для непрерывной работы с кодовым словом)
        """
        logger.info("Запуск прослушивания...")
        self.input_stream.start()
        logger.info("Прослушивание запущено")
        return self._listen_and_respond()
    
    def start_listening(self) -> str:
        """
        Начинает прослушивание аудиовхода и соответствующим образом реагирует при обнаружении активного голоса.
        Эта функция вернет транскрибированный текст после обнаружения паузы.
        Она использует функцию `transcribe`, предоставленную в конструкторе, для транскрибации аудио.
        
        Returns:
            str: Транскрибированный текст.
        """
        self.input_stream.start()
        logger.info("Запуск прослушивания...")
        logger.info("Прослушивание запущено")
        return self._listen_and_respond(returnText=True) # returnText=True указывает, что нужно вернуть текст

    def _listen_and_respond(self, returnText=False):
        """
        Прослушивает аудиовход и соответствующим образом реагирует при обнаружении кодового слова (если установлено).
        Если returnText=True, возвращает транскрибированный текст.
        """
        logger.info("Прослушивание...")
        while True:  # Бесконечный цикл, "приостанавливается", когда нет новых семплов
            sample, vad_confidence = self.sample_queue.get() # Получение семпла из очереди
            result = self._handle_audio_sample(sample, vad_confidence) # Обработка семпла

            if result: # Если есть результат (транскрибированный текст)
                if returnText:
                    # Если мы возвращаем текст и не запускаем прослушивание снова, мы можем сбросить рекордер без блокировки
                    threading.Thread(target=self.reset).start() # Сброс в отдельном потоке
                    # self.reset() # Синхронный сброс (закомментировано)
                    return result
                self.reset() # Сброс состояния
                self.input_stream.start() # Перезапуск потока

    def _handle_audio_sample(self, sample, vad_confidence):
        """
        Обрабатывает каждый аудиосемпл.
        """
        if not self.recording_started: # Если запись еще не началась
            self._manage_pre_activation_buffer(sample, vad_confidence) # Управление буфером до активации
        else: # Если запись уже идет
            return self._process_activated_audio(sample, vad_confidence) # Обработка активированного аудио

    def _manage_pre_activation_buffer(self, sample, vad_confidence):
        """
        Управляет буфером аудиосемплов до активации (т.е. до обнаружения голоса).
        """
        if self.buffer.full():
            self.buffer.get()  # Удаление самого старого семпла, чтобы освободить место для нового
        self.buffer.put(sample) # Добавление нового семпла в буфер

        if vad_confidence:  # Обнаружена голосовая активность
            self.samples = list(self.buffer.queue) # Копирование буфера в основной список семплов
            self.recording_started = True # Установка флага начала записи

    def _process_activated_audio(self, sample: np.ndarray, vad_confidence: bool):
        """
        Обрабатывает аудиосемплы после активации (т.е. после обнаружения кодового слова или начала речи).

        Использует лимит паузы для определения момента обработки обнаруженного аудио. Это делается для
        того, чтобы гарантировать захват всего предложения перед обработкой, включая небольшие паузы.
        """

        self.samples.append(sample) # Добавление семпла в список

        if not vad_confidence: # Если голосовая активность не обнаружена
            self.gap_counter += 1 # Увеличение счетчика пауз
            if self.gap_counter >= PAUSE_LIMIT // VAD_SIZE: # Если достигнут лимит пауз
                return self._process_detected_audio() # Обработка обнаруженного аудио
        else: # Если голосовая активность обнаружена
            self.gap_counter = 0 # Сброс счетчика пауз

    # def _wakeword_detected(self, text: str) -> bool:
    #     """
    #     Вычисляет ближайшее расстояние Левенштейна от обнаруженного текста до кодового слова.

    #     Это используется, так как 'Glados' - не распространенное слово, и Whisper может иногда его неправильно расслышать.
    #     """
    #     words = text.split()
    #     closest_distance = min(
    #         [distance(word.lower(), self.wake_word) for word in words]
    #     )
    #     return closest_distance < SIMILARITY_THRESHOLD

    def _process_detected_audio(self):
        """
        Обрабатывает обнаруженное аудио и генерирует ответ (транскрипцию).
        """
        logger.info("Обнаружена пауза после речи. Обработка...")

        logger.info("Остановка прослушивания...")
        self.input_stream.stop() # Остановка аудиопотока
        

        detected_text = self.asr(self.samples) # Распознавание речи из собранных семплов

        if detected_text:
            logger.info(f"Обнаружено: '{detected_text}'")
            return detected_text

        # Эти две строки никогда не будут достигнуты, потому что я сделал так, чтобы функция возвращала обнаруженный текст,
        # поэтому функция reset будет вызвана в функции _listen_and_respond
        # self.reset()
        # self.input_stream.start()

    def asr(self, samples: List[np.ndarray]) -> str:
        """
        Выполняет автоматическое распознавание речи на собранных семплах.
        """
        audio = np.concatenate(samples) # Объединение списка семплов в один массив numpy

        detected_text = self.transcribe(audio) # Транскрибация аудио
        return detected_text

    def reset(self):
        """
        Сбрасывает состояние записи и очищает буферы.
        """
        logger.info("Сброс рекордера...")
        self.recording_started = False # Сброс флага начала записи
        self.samples.clear() # Очистка списка семплов
        self.gap_counter = 0 # Сброс счетчика пауз
        with self.buffer.mutex: # Блокировка доступа к очереди буфера
            self.buffer.queue.clear() # Очистка очереди буфера




if __name__ == "__main__":
    # Пример использования (закомментирован)
    # demo = VoiceRecognition() # VoiceRecognition не определен здесь, вероятно, это должно быть VoiceRecognitionVAD
    # demo.start()
    # text = demo.transcribe_once() # transcribe_once не определен
    # print(text)
    pass # Добавлено для синтаксической корректности, если примеры закомментированы