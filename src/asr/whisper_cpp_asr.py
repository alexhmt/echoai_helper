from pywhispercpp.model import Model # Импорт класса Model из pywhispercpp

import numpy as np
from .asr_interface import ASRInterface # Импорт интерфейса ASR
from .asr_with_vad import VoiceRecognitionVAD # Импорт класса для распознавания с VAD


class VoiceRecognition(ASRInterface):
    """Класс для распознавания речи с использованием Whisper.cpp."""

    def __init__(
        self,
        model_name: str = "base", # Имя или путь к модели Whisper.cpp
        model_dir="asr/models", # Каталог, где хранятся или куда будут загружены модели
        language: str = "en", # Язык распознавания
        print_realtime: bool = False, # Печатать ли результаты в реальном времени
        print_progress: bool = False, # Печатать ли прогресс загрузки/обработки
        **kwargs # Дополнительные аргументы для конструктора Model
    ) -> None:
        """
        Инициализирует объект VoiceRecognition для Whisper.cpp.

        Args:
            model_name (str, optional): Имя или путь к модели. По умолчанию "base".
            model_dir (str, optional): Каталог моделей. По умолчанию "asr/models".
            language (str, optional): Язык. По умолчанию "en".
            print_realtime (bool, optional): Печать в реальном времени. По умолчанию False.
            print_progress (bool, optional): Печать прогресса. По умолчанию False.
            **kwargs: Дополнительные аргументы, передаваемые в конструктор pywhispercpp.model.Model.
        """
        
        self.model = Model(
            model=model_name,
            models_dir=model_dir,
            language=language,
            print_realtime=print_realtime,
            print_progress=print_progress,
            **kwargs
        )
        self.asr_with_vad = None # Экземпляр VoiceRecognitionVAD для использования с VAD
        
    def transcribe_with_local_vad(self) -> str:
        """
        Транскрибирует аудио с использованием локальной детекции голосовой активности (VAD).

        Returns:
            str: Распознанный текст.
        """
        if self.asr_with_vad is None:
            # Инициализация VoiceRecognitionVAD при первом вызове
            self.asr_with_vad = VoiceRecognitionVAD(self.transcribe_np)
        return self.asr_with_vad.start_listening() # Запуск прослушивания с VAD

    def transcribe_np(self, audio: np.ndarray) -> str:
        """
        Транскрибирует аудиоданные из массива numpy.

        Args:
            audio (np.ndarray): Массив numpy с аудиоданными для транскрибации.

        Returns:
            str: Распознанный текст.
        """
        # new_segment_callback=print означает, что каждый новый сегмент будет напечатан в консоль.
        # Это может быть полезно для отладки, но для продакшена, возможно, стоит передать другую функцию или None.
        segments = self.model.transcribe(audio, new_segment_callback=print) 
        full_text = ""
        for segment in segments: # segments здесь - это итератор объектов Segment
            full_text += segment.text # Конкатенация текста из каждого сегмента
        return full_text.strip() # Возврат полного текста без лишних пробелов

