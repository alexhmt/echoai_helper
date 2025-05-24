#!/usr/bin/env python3

"""Библиотека для выполнения распознавания речи с поддержкой нескольких движков и API, онлайн и офлайн."""

from __future__ import annotations

import aifc
import audioop
import base64
import collections
import hashlib
import hmac
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import wave
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import requests
except (ModuleNotFoundError, ImportError):
    pass

from .audio import AudioData, get_flac_converter
from .exceptions import (
    RequestError,
    TranscriptionFailed,
    TranscriptionNotReady,
    UnknownValueError,
    WaitTimeoutError,
)

__author__ = "Anthony Zhang (Uberi)"
__version__ = "3.11.0"
__license__ = "BSD"


class AudioSource(object):
#!/usr/bin/env python3

"""Библиотека для выполнения распознавания речи с поддержкой нескольких движков и API, онлайн и офлайн."""

from __future__ import annotations

import aifc
import audioop
import base64
import collections
import hashlib
import hmac
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import wave
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import requests # Попытка импортировать requests, если доступно
except (ModuleNotFoundError, ImportError):
    pass # Игнорировать, если не найдено

from .audio import AudioData, get_flac_converter # Импорт из локального модуля audio
from .exceptions import ( # Импорт исключений из локального модуля exceptions
    RequestError,
    TranscriptionFailed,
    TranscriptionNotReady,
    UnknownValueError,
    WaitTimeoutError,
)

__author__ = "Anthony Zhang (Uberi)"
__version__ = "3.11.0"
__license__ = "BSD"


class AudioSource(object):
    """Абстрактный класс, представляющий источник аудио."""
    def __init__(self):
        raise NotImplementedError("Это абстрактный класс")

    def __enter__(self):
        raise NotImplementedError("Это абстрактный класс")

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError("Это абстрактный класс")


class Microphone(AudioSource):
    """
    Создает новый экземпляр ``Microphone``, представляющий физический микрофон на компьютере. Подкласс ``AudioSource``.

    Вызовет ``AttributeError``, если у вас не установлен PyAudio (0.2.11 или новее).

    Если ``device_index`` не указан или равен ``None``, используется микрофон по умолчанию в качестве источника аудио. В противном случае ``device_index`` должен быть индексом устройства, используемого для аудиовхода.

    Индекс устройства — это целое число от 0 до ``pyaudio.get_device_count() - 1`` (предполагается, что мы предварительно использовали ``import pyaudio``) включительно. Он представляет аудиоустройство, такое как микрофон или динамик. Дополнительные сведения см. в `документации PyAudio <http://people.csail.mit.edu/hubert/pyaudio/docs/>`__.

    Аудио с микрофона записывается фрагментами по ``chunk_size`` семплов с частотой ``sample_rate`` семплов в секунду (Герц). Если не указано, значение ``sample_rate`` определяется автоматически из настроек микрофона системы.

    Более высокие значения ``sample_rate`` обеспечивают лучшее качество звука, но также требуют большей пропускной способности (и, следовательно, более медленного распознавания). Кроме того, некоторые процессоры, например, в старых моделях Raspberry Pi, могут не справляться, если это значение слишком велико.

    Более высокие значения ``chunk_size`` помогают избежать срабатывания на быстро меняющийся окружающий шум, но также делают обнаружение менее чувствительным. Это значение, как правило, следует оставить по умолчанию.
    """
    def __init__(self, device_index=None, sample_rate=None, chunk_size=1024, speaker=False, channels = 1):
        assert device_index is None or isinstance(device_index, int), "Индекс устройства должен быть None или целым числом"
        assert sample_rate is None or (isinstance(sample_rate, int) and sample_rate > 0), "Частота дискретизации должна быть None или положительным целым числом"
        assert isinstance(chunk_size, int) and chunk_size > 0, "Размер фрагмента должен быть положительным целым числом"

        # настройка PyAudio
        self.speaker=speaker
        self.pyaudio_module = self.get_pyaudio()
        audio = self.pyaudio_module.PyAudio()
        try:
            count = audio.get_device_count()  # получение количества устройств
            if device_index is not None:  # проверка, что индекс устройства находится в допустимом диапазоне
                assert 0 <= device_index < count, "Индекс устройства вне диапазона (доступно {} устройств; индекс устройства должен быть от 0 до {} включительно)".format(count, count - 1)
            if sample_rate is None:  # автоматическая установка частоты дискретизации на значение по умолчанию для оборудования, если не указано
                device_info = audio.get_device_info_by_index(device_index) if device_index is not None else audio.get_default_input_device_info()
                assert isinstance(device_info.get("defaultSampleRate"), (float, int)) and device_info["defaultSampleRate"] > 0, "От PyAudio получена неверная информация об устройстве: {}".format(device_info)
                sample_rate = int(device_info["defaultSampleRate"])
        finally:
            audio.terminate()

        self.device_index = device_index
        self.format = self.pyaudio_module.paInt16  # 16-битная целочисленная дискретизация
        self.SAMPLE_WIDTH = self.pyaudio_module.get_sample_size(self.format)  # размер каждого семпла
        self.SAMPLE_RATE = sample_rate  # частота дискретизации в Герцах
        self.CHUNK = chunk_size  # количество кадров, хранящихся в каждом буфере
        self.channels = channels

        self.audio = None
        self.stream = None

    @staticmethod
    def get_pyaudio():
        """
        Импортирует модуль pyaudio и проверяет его версию. Вызывает исключения, если pyaudio не найден или установлена неправильная версия.
        """
        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            raise AttributeError("Не удалось найти PyAudio; проверьте установку")
        from distutils.version import LooseVersion # Используется для сравнения версий
        if LooseVersion(pyaudio.__version__) < LooseVersion("0.2.11"):
            raise AttributeError("Требуется PyAudio 0.2.11 или новее (найдена версия {})".format(pyaudio.__version__))
        return pyaudio

    @staticmethod
    def list_microphone_names():
        """
        Возвращает список имен всех доступных микрофонов. Для микрофонов, имя которых не удалось получить, запись в списке содержит ``None``.

        Индекс имени каждого микрофона в возвращаемом списке совпадает с его индексом устройства при создании экземпляра ``Microphone`` — если вы хотите использовать микрофон с индексом 3 в возвращаемом списке, используйте ``Microphone(device_index=3)``.
        """
        audio = Microphone.get_pyaudio().PyAudio()
        try:
            result = []
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                result.append(device_info.get("name"))
        finally:
            audio.terminate()
        return result

    @staticmethod
    def list_working_microphones():
        """
        Возвращает словарь, сопоставляющий индексы устройств с именами микрофонов, для микрофонов, которые в данный момент улавливают звуки. При использовании этой функции убедитесь, что ваш микрофон не выключен, и произведите некоторый шум, чтобы он был определен как работающий.

        Каждый ключ в возвращаемом словаре можно передать конструктору ``Microphone`` для использования этого микрофона. Например, если возвращаемое значение равно ``{3: "HDA Intel PCH: ALC3232 Analog (hw:1,0)"}``, вы можете использовать ``Microphone(device_index=3)`` для этого микрофона.
        """
        pyaudio_module = Microphone.get_pyaudio()
        audio = pyaudio_module.PyAudio()
        try:
            result = {}
            for device_index in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(device_index)
                device_name = device_info.get("name")
                assert isinstance(device_info.get("defaultSampleRate"), (float, int)) and device_info["defaultSampleRate"] > 0, "От PyAudio получена неверная информация об устройстве: {}".format(device_info)
                try:
                    # чтение аудио
                    pyaudio_stream = audio.open(
                        input_device_index=device_index, channels=1, format=pyaudio_module.paInt16,
                        rate=int(device_info["defaultSampleRate"]), input=True
                    )
                    try:
                        buffer = pyaudio_stream.read(1024)
                        if not pyaudio_stream.is_stopped(): pyaudio_stream.stop_stream()
                    finally:
                        pyaudio_stream.close()
                except Exception:
                    continue

                # вычисление среднеквадратичного значения (RMS) аудио без смещения
                energy = -audioop.rms(buffer, 2)
                energy_bytes = bytes([energy & 0xFF, (energy >> 8) & 0xFF])
                debiased_energy = audioop.rms(audioop.add(buffer, energy_bytes * (len(buffer) // 2), 2), 2)

                if debiased_energy > 30:  # вероятно, это действительно аудио
                    result[device_index] = device_name
        finally:
            audio.terminate()
        return result

    def __enter__(self):
        assert self.stream is None, "Этот источник аудио уже используется в контекстном менеджере"
        self.audio = self.pyaudio_module.PyAudio()
        try:
            if self.speaker: # Если это динамик (для записи системных звуков)
                p = self.audio
                self.stream = Microphone.MicrophoneStream(
                    p.open(
                        input_device_index=self.device_index,
                        channels=self.channels,
                        format=self.format,
                        rate=self.SAMPLE_RATE,
                        frames_per_buffer=self.CHUNK,
                        input=True
                    )
                )
            else: # Обычный микрофон           
                self.stream = Microphone.MicrophoneStream(
                    self.audio.open(
                        input_device_index=self.device_index, channels=1, format=self.format,
                        rate=self.SAMPLE_RATE, frames_per_buffer=self.CHUNK, input=True,
                    )
                )
        except Exception:
            self.audio.terminate() # В случае ошибки освободить ресурсы PyAudio
            raise # Повторно вызвать исключение
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.stream: # Убедиться, что поток существует перед закрытием
                self.stream.close()
        finally:
            self.stream = None
            if self.audio: # Убедиться, что PyAudio объект существует
                self.audio.terminate()

    class MicrophoneStream(object):
        """Внутренний класс-оболочка для потока PyAudio."""
        def __init__(self, pyaudio_stream):
            self.pyaudio_stream = pyaudio_stream

        def read(self, size):
            """Читает данные из потока PyAudio."""
            return self.pyaudio_stream.read(size, exception_on_overflow=False) # exception_on_overflow=False для предотвращения ошибок при переполнении буфера

        def close(self):
            """Закрывает поток PyAudio."""
            try:
                # иногда, если поток не остановлен, закрытие потока вызывает исключение
                if not self.pyaudio_stream.is_stopped():
                    self.pyaudio_stream.stop_stream()
            finally:
                self.pyaudio_stream.close()


class AudioFile(AudioSource):
    """
    Создает новый экземпляр ``AudioFile`` из аудиофайла WAV/AIFF/FLAC ``filename_or_fileobject``. Подкласс ``AudioSource``.

    Если ``filename_or_fileobject`` является строкой, он интерпретируется как путь к аудиофайлу в файловой системе. В противном случае ``filename_or_fileobject`` должен быть файлоподобным объектом, таким как ``io.BytesIO`` или аналогичным.

    Обратите внимание, что функции, читающие из аудио (например, ``recognizer_instance.record`` или ``recognizer_instance.listen``), будут перемещаться вперед по потоку. Например, если вы выполните ``recognizer_instance.record(audiofile_instance, duration=10)`` дважды, в первый раз он вернет первые 10 секунд аудио, а во второй раз — 10 секунд аудио сразу после этого. Это всегда сбрасывается в начало при входе в контекст ``AudioFile``.

    Файлы WAV должны быть в формате PCM/LPCM; WAVE_FORMAT_EXTENSIBLE и сжатые WAV не поддерживаются и могут привести к неопределенному поведению.

    Поддерживаются форматы AIFF и AIFF-C (сжатый AIFF).

    Файлы FLAC должны быть в нативном формате FLAC; OGG-FLAC не поддерживается и может привести к неопределенному поведению.
    """

    def __init__(self, filename_or_fileobject):
        assert isinstance(filename_or_fileobject, (type(""), type(u""))) or hasattr(filename_or_fileobject, "read"), "Указанный аудиофайл должен быть строкой с именем файла или файлоподобным объектом"
        self.filename_or_fileobject = filename_or_fileobject
        self.stream = None # Поток аудиоданных
        self.DURATION = None # Длительность аудиофайла

        self.audio_reader = None # Объект для чтения аудиофайла
        self.little_endian = False # Флаг порядка байтов (little-endian)
        self.SAMPLE_RATE = None # Частота дискретизации
        self.CHUNK = None # Размер фрагмента для чтения
        self.FRAME_COUNT = None # Общее количество кадров

    def __enter__(self):
        assert self.stream is None, "Этот источник аудио уже используется в контекстном менеджере"
        try:
            # попытка прочитать файл как WAV
            self.audio_reader = wave.open(self.filename_or_fileobject, "rb")
            self.little_endian = True  # Формат RIFF WAV является little-endian (большинство операций ``audioop`` предполагают, что кадры хранятся в формате little-endian)
        except (wave.Error, EOFError):
            try:
                # попытка прочитать файл как AIFF
                self.audio_reader = aifc.open(self.filename_or_fileobject, "rb")
                self.little_endian = False  # Формат AIFF является big-endian
            except (aifc.Error, EOFError):
                # попытка прочитать файл как FLAC
                if hasattr(self.filename_or_fileobject, "read"): # Если это файлоподобный объект
                    flac_data = self.filename_or_fileobject.read()
                else: # Если это путь к файлу
                    with open(self.filename_or_fileobject, "rb") as f: flac_data = f.read()

                # запуск конвертера FLAC с данными FLAC для получения данных AIFF
                flac_converter = get_flac_converter()
                if os.name == "nt":  # в Windows указываем, что процесс должен запускаться без отображения консольного окна
                    startup_info = subprocess.STARTUPINFO()
                    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # указываем, что поле wShowWindow структуры `startup_info` содержит значение
                    startup_info.wShowWindow = subprocess.SW_HIDE  # указываем, что консольное окно должно быть скрыто
                else:
                    startup_info = None  # информация о запуске по умолчанию
                process = subprocess.Popen([
                    flac_converter,
                    "--stdout", "--totally-silent",  # вывод результирующего файла AIFF в stdout и гарантия отсутствия смешивания с выводом программы
                    "--decode", "--force-aiff-format",  # декодирование файла FLAC в файл AIFF
                    "-",  # содержимое входного файла FLAC будет передано через stdin
                ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startup_info)
                aiff_data, _ = process.communicate(flac_data) # Получение данных AIFF
                aiff_file = io.BytesIO(aiff_data) # Создание файлоподобного объекта из данных AIFF
                try:
                    self.audio_reader = aifc.open(aiff_file, "rb")
                except (aifc.Error, EOFError):
                    raise ValueError("Аудиофайл не может быть прочитан как PCM WAV, AIFF/AIFF-C или Native FLAC; проверьте, не поврежден ли файл или не находится ли он в другом формате")
                self.little_endian = False  # Формат AIFF является big-endian
        assert 1 <= self.audio_reader.getnchannels() <= 2, "Аудио должно быть моно или стерео"
        self.SAMPLE_WIDTH = self.audio_reader.getsampwidth() # Ширина семпла

        # 24-битное аудио требует специальной обработки для старых версий Python (обход проблемы https://bugs.python.org/issue12866)
        samples_24_bit_pretending_to_be_32_bit = False
        if self.SAMPLE_WIDTH == 3:  # 24-битное аудио
            try: audioop.bias(b"", self.SAMPLE_WIDTH, 0)  # проверка поддержки этой ширины семпла (например, ``audioop`` в Python 3.3 и ниже не поддерживает ширину семпла 3, в то время как Python 3.4+ поддерживает)
            except audioop.error:  # эта версия audioop не поддерживает 24-битное аудио (вероятно, Python 3.3 или младше)
                samples_24_bit_pretending_to_be_32_bit = True  # хотя экземпляр ``AudioFile`` будет внешне выглядеть как 32-битный, внутренне он будет 24-битным
                self.SAMPLE_WIDTH = 4  # экземпляр ``AudioFile`` теперь должен представлять себя как 32-битный поток, так как мы будем преобразовывать его в 32-битный на лету при чтении

        self.SAMPLE_RATE = self.audio_reader.getframerate() # Частота дискретизации
        self.CHUNK = 4096 # Размер фрагмента
        self.FRAME_COUNT = self.audio_reader.getnframes() # Количество кадров
        self.DURATION = self.FRAME_COUNT / float(self.SAMPLE_RATE) # Длительность
        self.stream = AudioFile.AudioFileStream(self.audio_reader, self.little_endian, samples_24_bit_pretending_to_be_32_bit) # Создание потока
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self.filename_or_fileobject, "read"):  # закрывать файл только в том случае, если он был открыт этим классом (если файл изначально был указан как путь)
            self.audio_reader.close()
        self.stream = None
        self.DURATION = None

    class AudioFileStream(object):
        """Внутренний класс-оболочка для потока аудиофайла."""
        def __init__(self, audio_reader, little_endian, samples_24_bit_pretending_to_be_32_bit):
            self.audio_reader = audio_reader  # объект аудиофайла (например, экземпляр `wave.Wave_read`)
            self.little_endian = little_endian  # является ли аудиоданные little-endian (при работе с big-endian данными нам придется преобразовывать их в little-endian перед обработкой)
            self.samples_24_bit_pretending_to_be_32_bit = samples_24_bit_pretending_to_be_32_bit  # истинно, если аудио 24-битное, но 24-битное аудио не поддерживается, поэтому нам приходится делать вид, что это 32-битное аудио, и преобразовывать его на лету

        def read(self, size=-1):
            """Читает данные из потока аудиофайла."""
            buffer = self.audio_reader.readframes(self.audio_reader.getnframes() if size == -1 else size)
            if not isinstance(buffer, bytes): buffer = b""  # обход проблемы https://bugs.python.org/issue24608

            sample_width = self.audio_reader.getsampwidth()
            if not self.little_endian:  # формат big-endian, преобразуем в little-endian на лету
                if hasattr(audioop, "byteswap"):  # ``audioop.byteswap`` был добавлен только в Python 3.4 (кстати, это также означает, что нам не нужно беспокоиться о неподдерживаемом 24-битном аудио, так как Python 3.4+ всегда имеет эту функциональность)
                    buffer = audioop.byteswap(buffer, sample_width)
                else:  # вручную инвертируем байты каждого семпла, что медленнее, но достаточно хорошо работает в качестве запасного варианта
                    buffer = buffer[sample_width - 1::-1] + b"".join(buffer[i + sample_width:i:-1] for i in range(sample_width - 1, len(buffer), sample_width))

            # обход проблемы https://bugs.python.org/issue12866
            if self.samples_24_bit_pretending_to_be_32_bit:  # нам нужно преобразовать семплы из 24-битных в 32-битные, прежде чем мы сможем обрабатывать их функциями ``audioop``
                buffer = b"".join(b"\x00" + buffer[i:i + sample_width] for i in range(0, len(buffer), sample_width))  # так как мы в little-endian, мы добавляем нулевой байт в начало каждого 24-битного семпла, чтобы получить 32-битный семпл
                sample_width = 4  # убедимся, что теперь мы обрабатываем буфер как 32-битное аудио, после преобразования из 24-битного аудио
            if self.audio_reader.getnchannels() != 1:  # стерео аудио
                buffer = audioop.tomono(buffer, sample_width, 1, 1)  # преобразование стерео аудиоданных в моно
            return buffer


class Recognizer(AudioSource): # Recognizer не должен наследоваться от AudioSource, это ошибка в оригинальном коде, но сохраняем для совместимости перевода.
    """Класс Recognizer представляет собой набор функций для распознавания речи."""
    def __init__(self):
        """
        Создает новый экземпляр ``Recognizer``, который представляет собой набор функций распознавания речи.
        """
        self.energy_threshold = 300  # минимальная энергия звука, чтобы считать его записью
        self.dynamic_energy_threshold = True # динамическая подстройка порога энергии
        self.dynamic_energy_adjustment_damping = 0.15 # коэффициент затухания для динамической подстройки порога энергии
        self.dynamic_energy_ratio = 1.5 # соотношение для динамической подстройки порога энергии
        self.pause_threshold = 0.8  # секунды тишины перед тем, как фраза будет считаться завершенной
        self.operation_timeout = None  # секунды до истечения времени ожидания внутренней операции (например, API-запроса), или ``None`` для отсутствия тайм-аута

        self.phrase_threshold = 0.3  # минимальное количество секунд речи, прежде чем мы будем считать речь фразой - значения ниже этого игнорируются (для отфильтровывания щелчков и хлопков)
        self.non_speaking_duration = 0.5  # секунды тишины, которые нужно сохранить с обеих сторон записи

    def record(self, source, duration=None, offset=None):
        """
        Записывает до ``duration`` секунд аудио из ``source`` (экземпляр ``AudioSource``), начиная с ``offset`` (или с начала, если не указано) в экземпляр ``AudioData``, который и возвращает.

        Если ``duration`` не указан, запись будет продолжаться до тех пор, пока не закончится аудиовход.
        """
        assert isinstance(source, AudioSource), "Источник должен быть аудиоисточником"
        assert source.stream is not None, "Аудиоисточник должен быть открыт перед записью, см. документацию для ``AudioSource``; используете ли вы ``source`` вне оператора ``with``?"

        frames = io.BytesIO() # Буфер для кадров
        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE # Длительность одного буфера в секундах
        elapsed_time = 0 # Прошедшее время записи
        offset_time = 0 # Время смещения
        offset_reached = False # Флаг достижения смещения
        while True:  # цикл по общему количеству необходимых фрагментов
            if offset and not offset_reached: # Если есть смещение и оно еще не достигнуто
                offset_time += seconds_per_buffer
                if offset_time > offset:
                    offset_reached = True

            buffer = source.stream.read(source.CHUNK) # Чтение фрагмента из потока
            if len(buffer) == 0: break # Если буфер пуст, значит поток закончился

            if offset_reached or not offset: # Если смещение достигнуто или его нет
                elapsed_time += seconds_per_buffer
                if duration and elapsed_time > duration: break # Если достигнута указанная длительность

                frames.write(buffer) # Запись буфера в общий буфер кадров

        frame_data = frames.getvalue() # Получение всех записанных данных
        frames.close()
        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH) # Возврат объекта AudioData

    def adjust_for_ambient_noise(self, source, duration=1):
        """
        Динамически настраивает порог энергии, используя аудио из ``source`` (экземпляр ``AudioSource``) для учета окружающего шума.

        Предназначен для калибровки порога энергии с уровнем окружающего шума. Следует использовать на участках аудио без речи — остановится раньше, если будет обнаружена речь.

        Параметр ``duration`` — это максимальное количество секунд, в течение которых он будет динамически настраивать порог перед возвратом. Это значение должно быть не менее 0.5, чтобы получить репрезентативную выборку окружающего шума.
        """
        assert isinstance(source, AudioSource), "Источник должен быть аудиоисточником"
        assert source.stream is not None, "Аудиоисточник должен быть открыт перед настройкой, см. документацию для ``AudioSource``; используете ли вы ``source`` вне оператора ``with``?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0

        # настройка порога энергии до начала фразы
        while True:
            elapsed_time += seconds_per_buffer
            if elapsed_time > duration: break # Прерывание, если превышена длительность
            buffer = source.stream.read(source.CHUNK)
            energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # энергия аудиосигнала

            # динамическая настройка порога энергии с использованием асимметричного взвешенного среднего
            damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # учет различных размеров фрагментов и частот дискретизации
            target_energy = energy * self.dynamic_energy_ratio
            self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

    def snowboy_wait_for_hot_word(self, snowboy_location, snowboy_hot_word_files, source, timeout=None):
        """Ожидает произнесения кодового слова с использованием Snowboy."""
        # загрузка библиотеки snowboy (НЕ ПОТОКОБЕЗОПАСНО)
        sys.path.append(snowboy_location)
        import snowboydetect # type: ignore
        sys.path.pop()

        detector = snowboydetect.SnowboyDetect(
            resource_filename=os.path.join(snowboy_location, "resources", "common.res").encode(),
            model_str=",".join(snowboy_hot_word_files).encode()
        )
        detector.SetAudioGain(1.0) # Установка усиления звука
        detector.SetSensitivity(",".join(["0.4"] * len(snowboy_hot_word_files)).encode()) # Установка чувствительности
        snowboy_sample_rate = detector.SampleRate() # Получение частоты дискретизации Snowboy

        elapsed_time = 0
        seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
        resampling_state = None # Состояние для передискретизации

        # буферы, способные вместить 5 секунд исходного аудио
        five_seconds_buffer_count = int(math.ceil(5 / seconds_per_buffer))
        # буферы, способные вместить 0.5 секунды передискретизированного аудио
        half_second_buffer_count = int(math.ceil(0.5 / seconds_per_buffer))
        frames = collections.deque(maxlen=five_seconds_buffer_count) # Очередь для исходных кадров
        resampled_frames = collections.deque(maxlen=half_second_buffer_count) # Очередь для передискретизированных кадров
        # интервал проверки snowboy
        check_interval = 0.05
        last_check = time.time() # Время последней проверки
        while True:
            elapsed_time += seconds_per_buffer
            if timeout and elapsed_time > timeout:
                raise WaitTimeoutError("Время ожидания прослушивания истекло в ожидании произнесения кодового слова")

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break  # достигнут конец потока
            frames.append(buffer)

            # передискретизация аудио до требуемой частоты дискретизации
            resampled_buffer, resampling_state = audioop.ratecv(buffer, source.SAMPLE_WIDTH, 1, source.SAMPLE_RATE, snowboy_sample_rate, resampling_state)
            resampled_frames.append(resampled_buffer)
            if time.time() - last_check > check_interval:
                # запуск Snowboy на передискретизированном аудио
                snowboy_result = detector.RunDetection(b"".join(resampled_frames))
                assert snowboy_result != -1, "Ошибка инициализации потоков или чтения аудиоданных"
                if snowboy_result > 0: break  # найдено кодовое слово
                resampled_frames.clear()
                last_check = time.time()

        return b"".join(frames), elapsed_time # Возврат записанных кадров и времени

    def listen(self, source, timeout=None, phrase_time_limit=None, snowboy_configuration=None, stream=False):
        """
        Записывает одну фразу из ``source`` (экземпляр ``AudioSource``) в экземпляр ``AudioData``, который и возвращает.

        Если аргумент ключевого слова ``stream`` равен ``True``, метод ``listen()`` будет возвращать (yield) экземпляры ``AudioData``, представляющие фрагменты аудиоданных по мере их обнаружения. Первый возвращенный экземпляр ``AudioData`` представляет первый буфер фразы, а последний возвращенный экземпляр ``AudioData`` представляет последний буфер фразы. Если ``stream`` равен ``False``, метод вернет один экземпляр ``AudioData``, представляющий всю фразу.

        Это делается путем ожидания, пока энергия звука не превысит ``recognizer_instance.energy_threshold`` (пользователь начал говорить), а затем записи до тех пор, пока не встретится ``recognizer_instance.pause_threshold`` секунд тишины или пока не закончится аудиовход. Конечная тишина не включается.

        Параметр ``timeout`` — это максимальное количество секунд, в течение которых будет ожидаться начало фразы, прежде чем сдаться и вызвать исключение ``speech_recognition.WaitTimeoutError``. Если ``timeout`` равен ``None``, тайм-аута ожидания не будет.

        Параметр ``phrase_time_limit`` — это максимальное количество секунд, в течение которых будет разрешено продолжаться фразе, прежде чем остановиться и вернуть часть фразы, обработанную до достижения лимита времени. Результирующее аудио будет фразой, обрезанной по лимиту времени. Если ``phrase_timeout`` равен ``None``, лимита времени для фразы не будет.

        Параметр ``snowboy_configuration`` позволяет интегрироваться с `Snowboy <https://snowboy.kitt.ai/>`__, автономным, высокоточным и энергоэффективным движком распознавания кодовых слов. При использовании эта функция будет приостановлена до тех пор, пока Snowboy не обнаружит кодовое слово, после чего она возобновит работу. Этот параметр должен быть либо ``None`` для отключения поддержки Snowboy, либо кортежем вида ``(SNOWBOY_LOCATION, LIST_OF_HOT_WORD_FILES)``, где ``SNOWBOY_LOCATION`` — это путь к корневому каталогу Snowboy, а ``LIST_OF_HOT_WORD_FILES`` — это список путей к файлам конфигурации кодовых слов Snowboy (формат `*.pmdl` или `*.umdl`).

        Эта операция всегда завершится в течение ``timeout + phrase_timeout`` секунд, если оба параметра являются числами, либо вернув аудиоданные, либо вызвав исключение ``speech_recognition.WaitTimeoutError``.
        """
        result = self._listen(source, timeout, phrase_time_limit, snowboy_configuration, stream)
        if not stream: # Если не потоковый режим, вернуть первую (и единственную) часть
            for a in result:
                return a
        return result # В потоковом режиме вернуть генератор

    def _listen(self, source, timeout=None, phrase_time_limit=None, snowboy_configuration=None, stream=False):
        """Внутренний метод для прослушивания аудио."""
        assert isinstance(source, AudioSource), "Источник должен быть аудиоисточником"
        assert source.stream is not None, "Аудиоисточник должен быть открыт перед прослушиванием, см. документацию для ``AudioSource``; используете ли вы ``source`` вне оператора ``with``?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0
        if snowboy_configuration is not None:
            assert os.path.isfile(os.path.join(snowboy_configuration[0], "snowboydetect.py")), "``snowboy_configuration[0]`` должен быть корневым каталогом Snowboy, содержащим ``snowboydetect.py``"
            for hot_word_file in snowboy_configuration[1]:
                assert os.path.isfile(hot_word_file), "``snowboy_configuration[1]`` должен быть списком файлов конфигурации кодовых слов Snowboy"

        seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
        pause_buffer_count = int(math.ceil(self.pause_threshold / seconds_per_buffer))  # количество буферов тишины во время фразы, прежде чем фраза будет считаться завершенной
        phrase_buffer_count = int(math.ceil(self.phrase_threshold / seconds_per_buffer))  # минимальное количество буферов речи, прежде чем мы будем считать речь фразой
        non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / seconds_per_buffer))  # максимальное количество буферов тишины, которые нужно сохранить до и после фразы

        # чтение аудиовхода для фраз до тех пор, пока не найдется достаточно длинная фраза
        elapsed_time = 0  # количество секунд прочитанного аудио
        buffer = b""  # пустой буфер означает, что поток закончился и данных для чтения больше нет
        while True:
            frames = collections.deque() # Очередь для хранения кадров текущей фразы

            if snowboy_configuration is None: # Если Snowboy не используется
                # сохранение аудиовхода до начала фразы
                while True:
                    # обработка слишком долгого ожидания фразы путем вызова исключения
                    elapsed_time += seconds_per_buffer
                    if timeout and elapsed_time > timeout:
                        raise WaitTimeoutError("Время ожидания прослушивания истекло в ожидании начала фразы")

                    buffer = source.stream.read(source.CHUNK)
                    if len(buffer) == 0: break  # достигнут конец потока
                    frames.append(buffer)
                    if len(frames) > non_speaking_buffer_count:  # гарантируем, что мы храним только необходимое количество буферов тишины
                        frames.popleft()

                    # определение начала речи на аудиовходе
                    energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # энергия аудиосигнала
                    if energy > self.energy_threshold: break # Если энергия выше порога, начинаем запись фразы

                    # динамическая настройка порога энергии с использованием асимметричного взвешенного среднего
                    if self.dynamic_energy_threshold:
                        damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # учет различных размеров фрагментов и частот дискретизации
                        target_energy = energy * self.dynamic_energy_ratio
                        self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)
            else: # Если используется Snowboy
                # чтение аудиовхода до произнесения кодового слова
                snowboy_location, snowboy_hot_word_files = snowboy_configuration
                buffer, delta_time = self.snowboy_wait_for_hot_word(snowboy_location, snowboy_hot_word_files, source, timeout)
                elapsed_time += delta_time
                if len(buffer) == 0: break  # достигнут конец потока
                frames.append(buffer)

            # чтение аудиовхода до конца фразы
            pause_count, phrase_count = 0, 0
            phrase_start_time = elapsed_time # Время начала фразы

            if stream: # Если потоковый режим
                # возвращаем первый буфер фразы
                yield AudioData(b"".join(frames), source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                frames.clear() # Очищаем кадры, так как они уже были переданы

            while True:
                # обработка слишком длинной фразы путем обрезки аудио
                elapsed_time += seconds_per_buffer
                if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
                    break # Прерывание, если превышен лимит времени фразы

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break  # достигнут конец потока
                frames.append(buffer)
                phrase_count += 1

                # проверка, прекратилась ли речь на время, превышающее порог паузы, на аудиовходе
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # единичная энергия аудиосигнала в буфере
                if energy > self.energy_threshold: # Если есть речь
                    pause_count = 0
                else: # Если тишина
                    pause_count += 1
                if pause_count > pause_buffer_count:  # конец фразы
                    break

                # динамическая настройка порога энергии с использованием асимметричного взвешенного среднего
                if self.dynamic_energy_threshold:
                    damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer
                    target_energy = energy * self.dynamic_energy_ratio
                    self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

                if stream: # Если потоковый режим
                    # возвращаем текущий фрагмент аудиоданных, обернутый в AudioData
                    yield AudioData(buffer, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

            # проверка длины обнаруженной фразы и повторная попытка прослушивания, если фраза слишком короткая
            phrase_count -= pause_count  # исключение буферов паузы перед фразой
            if phrase_count >= phrase_buffer_count or len(buffer) == 0: break  # фраза достаточно длинная или достигнут конец потока, поэтому прекращаем прослушивание

        if stream: # Если потоковый режим
            # возвращаем последний буфер фразы.
            yield AudioData(buffer, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
        else: # Если не потоковый режим
            # получение данных кадра
            for i in range(pause_count - non_speaking_buffer_count): frames.pop()  # удаление лишних кадров тишины в конце
            frame_data = b"".join(frames)
            # возвращаем всю фразу как один экземпляр AudioData
            yield AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def listen_in_background(self, source, callback, phrase_time_limit=None):
        """
        Запускает поток для многократной записи фраз из ``source`` (экземпляр ``AudioSource``) в экземпляр ``AudioData`` и вызывает ``callback`` с этим экземпляром ``AudioData`` сразу после обнаружения каждой фразы.

        Возвращает объект функции, который при вызове запрашивает остановку фонового потока прослушивания. Фоновый поток является демоном и не будет препятствовать выходу программы, если нет других не-демонских потоков. Функция принимает один параметр, ``wait_for_stop``: если истинно, функция будет ждать остановки фонового прослушивателя перед возвратом, в противном случае она вернется немедленно, и фоновый поток прослушивания может все еще работать в течение секунды или двух после этого. Кроме того, если вы используете истинное значение для ``wait_for_stop``, вы должны вызывать функцию из того же потока, из которого вы изначально вызвали ``listen_in_background``.

        Распознавание фраз использует тот же механизм, что и ``recognizer_instance.listen(source)``. Параметр ``phrase_time_limit`` работает так же, как и параметр ``phrase_time_limit`` для ``recognizer_instance.listen(source)``.

        Параметр ``callback`` — это функция, которая должна принимать два параметра — ``recognizer_instance`` и экземпляр ``AudioData``, представляющий захваченное аудио. Обратите внимание, что функция ``callback`` будет вызвана из не основного потока.
        """
        assert isinstance(source, AudioSource), "Источник должен быть аудиоисточником"
        running = [True] # Флаг для управления работой потока

        def threaded_listen():
            """Функция, выполняемая в отдельном потоке для прослушивания."""
            with source as s: # Использование источника как контекстного менеджера
                while running[0]: # Пока флаг running истинен
                    try:  # прослушивание в течение 1 секунды, затем снова проверка, была ли вызвана функция остановки
                        audio = self.listen(s, timeout=1, phrase_time_limit=phrase_time_limit) # Уменьшен timeout для частой проверки running
                    except WaitTimeoutError:  # время ожидания прослушивания истекло, просто пробуем снова
                        pass
                    else: # Если аудио успешно захвачено
                        if running[0]: callback(self, audio) # Вызов callback, если все еще работаем

        def stopper(wait_for_stop=True):
            """Функция для остановки фонового прослушивания."""
            running[0] = False # Установка флага в False для остановки цикла в потоке
            if wait_for_stop: # Если нужно дождаться завершения потока
                listener_thread.join()  # блокировка до завершения фонового потока, что может занять около 1 секунды

        listener_thread = threading.Thread(target=threaded_listen) # Создание потока
        listener_thread.daemon = True # Установка потока как демона
        listener_thread.start() # Запуск потока
        return stopper # Возврат функции остановки

    def recognize_sphinx(self, audio_data, language="en-US", keyword_entries=None, grammar=None, show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя CMU Sphinx.

        Язык распознавания определяется параметром ``language``, тегом языка RFC5646, например, ``"en-US"`` или ``"en-GB"``, по умолчанию используется американский английский. "Из коробки" поддерживается только ``en-US``. См. `Примечания по использованию PocketSphinx <https://github.com/Uberi/speech_recognition/blob/master/reference/pocketsphinx.rst>`__ для получения информации об установке других языков. Этот документ также включен в ``reference/pocketsphinx.rst``. Параметр ``language`` также может быть кортежем путей файловой системы вида ``(каталог_акустических_параметров, файл_языковой_модели, файл_фонемного_словаря)`` - это позволяет загружать произвольные модели Sphinx.

        Если указано, ключевые слова для поиска определяются параметром ``keyword_entries``, итерируемым объектом кортежей вида ``(ключевое_слово, чувствительность)``, где ``ключевое_слово`` - это фраза, а ``чувствительность`` - насколько чувствительным должен быть распознаватель к этой фразе, по шкале от 0 (очень нечувствительный, больше ложных отрицаний) до 1 (очень чувствительный, больше ложных срабатываний) включительно. Если не указано или ``None``, ключевые слова не используются, и Sphinx просто транскрибирует любые распознанные слова. Указание ``keyword_entries`` более точно, чем просто поиск тех же ключевых слов в транскрипциях без использования ключевых слов, потому что Sphinx точно знает, какие звуки искать.

        Sphinx также может обрабатывать грамматики FSG или JSGF. Параметр ``grammar`` ожидает путь к файлу грамматики. Обратите внимание, что если передана грамматика JSGF, грамматика FSG будет создана в том же месте для ускорения выполнения при следующем запуске. Если переданы ``keyword_entries``, содержимое ``grammar`` будет проигнорировано.

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно false (по умолчанию). В противном случае возвращает объект Sphinx ``pocketsphinx.pocketsphinx.Decoder``, полученный в результате распознавания.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если есть какие-либо проблемы с установкой Sphinx.
        """
        assert isinstance(audio_data, AudioData), "``audio_data`` должен быть аудиоданными"
        assert isinstance(language, str) or (isinstance(language, tuple) and len(language) == 3), "``language`` должен быть строкой или 3-кортежем путей к файлам данных Sphinx вида ``(акустические_параметры, языковая_модель, фонемный_словарь)``"
        assert keyword_entries is None or all(isinstance(keyword, (type(""), type(u""))) and 0 <= sensitivity <= 1 for keyword, sensitivity in keyword_entries), "``keyword_entries`` должен быть ``None`` или списком пар строк и чисел от 0 до 1"

        # импорт модуля распознавания речи PocketSphinx
        try:
            from pocketsphinx import FsgModel, Jsgf, pocketsphinx # type: ignore

        except ImportError:
            raise RequestError("Отсутствует модуль PocketSphinx: убедитесь, что PocketSphinx настроен правильно.")
        except ValueError: # pragma: no cover
            raise RequestError("Неправильная установка PocketSphinx; попробуйте переустановить PocketSphinx версии 0.0.9 или новее.")
        if not hasattr(pocketsphinx, "Decoder") or not hasattr(pocketsphinx.Decoder, "default_config"): # pragma: no cover
            raise RequestError("Устаревшая установка PocketSphinx; убедитесь, что у вас PocketSphinx версии 0.0.9 или новее.")

        if isinstance(language, str):  # каталог, содержащий языковые данные
            language_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pocketsphinx-data", language)
            if not os.path.isdir(language_directory):
                raise RequestError("Отсутствует каталог языковых данных PocketSphinx: \"{}\"".format(language_directory))
            acoustic_parameters_directory = os.path.join(language_directory, "acoustic-model")
            language_model_file = os.path.join(language_directory, "language-model.lm.bin")
            phoneme_dictionary_file = os.path.join(language_directory, "pronounciation-dictionary.dict")
        else:  # 3-кортеж путей к файлам данных Sphinx
            acoustic_parameters_directory, language_model_file, phoneme_dictionary_file = language
        if not os.path.isdir(acoustic_parameters_directory):
            raise RequestError("Отсутствует каталог параметров языковой модели PocketSphinx: \"{}\"".format(acoustic_parameters_directory))
        if not os.path.isfile(language_model_file):
            raise RequestError("Отсутствует файл языковой модели PocketSphinx: \"{}\"".format(language_model_file))
        if not os.path.isfile(phoneme_dictionary_file):
            raise RequestError("Отсутствует файл фонемного словаря PocketSphinx: \"{}\"".format(phoneme_dictionary_file))

        # создание объекта декодера
        config = pocketsphinx.Decoder.default_config()
        config.set_string("-hmm", acoustic_parameters_directory)  # установка пути к файлам параметров скрытой марковской модели (HMM)
        config.set_string("-lm", language_model_file)
        config.set_string("-dict", phoneme_dictionary_file)
        config.set_string("-logfn", os.devnull)  # отключение логирования (логирование вызывает нежелательный вывод в терминале)
        decoder = pocketsphinx.Decoder(config)

        # получение аудиоданных
        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)  # включенные языковые модели требуют, чтобы аудио было 16-битным моно 16 кГц в формате little-endian

        # получение результатов распознавания
        if keyword_entries is not None:  # явно указанный набор ключевых слов
            with PortableNamedTemporaryFile("w") as f:
                # генерация файла ключевых слов - документация Sphinx рекомендует чувствительность от 1e-50 до 1e-5
                f.writelines("{} /1e{}/\n".format(keyword, 100 * sensitivity - 110) for keyword, sensitivity in keyword_entries)
                f.flush()

                # выполнение распознавания речи с файлом ключевых слов (это находится внутри контекстного менеджера, поэтому файл не удаляется до завершения)
                decoder.set_kws("keywords", f.name)
                decoder.set_search("keywords")
        elif grammar is not None:  # путь к грамматике FSG или JSGF
            if not os.path.exists(grammar):
                raise ValueError("Грамматика '{0}' не существует.".format(grammar))
            grammar_path = os.path.abspath(os.path.dirname(grammar))
            grammar_name = os.path.splitext(os.path.basename(grammar))[0]
            fsg_path = "{0}/{1}.fsg".format(grammar_path, grammar_name)
            if not os.path.exists(fsg_path):  # создание грамматики FSG, если она недоступна
                jsgf = Jsgf(grammar)
                rule = jsgf.get_rule("{0}.{0}".format(grammar_name))
                fsg = jsgf.build_fsg(rule, decoder.get_logmath(), 7.5)
                fsg.writefile(fsg_path)
            else:
                fsg = FsgModel(fsg_path, decoder.get_logmath(), 7.5)
            decoder.set_fsg(grammar_name, fsg)
            decoder.set_search(grammar_name)

        decoder.start_utt()  # начало обработки высказывания
        decoder.process_raw(raw_data, False, True)  # обработка аудиоданных с включенным распознаванием (no_search = False), как полное высказывание (full_utt = True)
        decoder.end_utt()  # остановка обработки высказывания

        if show_all: return decoder # Возврат объекта декодера, если show_all=True

        # возврат результатов
        hypothesis = decoder.hyp()
        if hypothesis is not None: return hypothesis.hypstr
        raise UnknownValueError()  # транскрипции недоступны

    def recognize_google_cloud(self, audio_data, credentials_json=None, language="en-US", preferred_phrases=None, show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Google Cloud Speech API.

        Эта функция требует учетной записи Google Cloud Platform; см. `Краткое руководство по Google Cloud Speech API <https://cloud.google.com/speech/docs/getting-started>`__ для получения подробной информации и инструкций. В основном, создайте проект, включите биллинг для проекта, включите Google Cloud Speech API для проекта и настройте учетные данные ключа сервисного аккаунта для проекта. Результатом является JSON-файл, содержащий учетные данные API. Текстовое содержимое этого JSON-файла указывается параметром ``credentials_json``. Если не указано, библиотека попытается автоматически `найти JSON-файл учетных данных API по умолчанию <https://developers.google.com/identity/protocols/application-default-credentials>`__.

        Язык распознавания определяется параметром ``language``, который является тегом языка BCP-47, например, ``"en-US"`` (американский английский). Список поддерживаемых тегов языков можно найти в `документации Google Cloud Speech API <https://cloud.google.com/speech/docs/languages>`__.

        Если ``preferred_phrases`` является итерируемым объектом строковых фраз, эти фразы будут с большей вероятностью распознаны по сравнению с похоже звучащими альтернативами. Это полезно для таких вещей, как распознавание ключевых слов/команд или добавление новых фраз, которых нет в словаре Google. Обратите внимание, что API накладывает определенные `ограничения на список строковых фраз <https://cloud.google.com/speech/limits#content>`__.

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно False (по умолчанию). В противном случае возвращает необработанный ответ API в виде словаря JSON.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если операция распознавания речи не удалась, если учетные данные недействительны или если нет подключения к Интернету.
        """
        assert isinstance(audio_data, AudioData), "``audio_data`` должен быть аудиоданными"
        if credentials_json is None: # Проверка наличия учетных данных
            assert os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') is not None, "Учетные данные Google Cloud не найдены. Установите переменную окружения GOOGLE_APPLICATION_CREDENTIALS."
        assert isinstance(language, str), "``language`` должен быть строкой"
        assert preferred_phrases is None or all(isinstance(phrase, (type(""), type(u""))) for phrase in preferred_phrases), "``preferred_phrases`` должен быть списком строк"


        try:
            import socket # Для проверки таймаута сокета по умолчанию

            from google.api_core.exceptions import GoogleAPICallError # Исключения Google API
            from google.cloud import speech # Клиент Google Cloud Speech
        except ImportError:
            raise RequestError('Отсутствует модуль google-cloud-speech: убедитесь, что google-cloud-speech настроен правильно.')

        if credentials_json is not None: # Использование JSON-файла учетных данных, если предоставлен
            client = speech.SpeechClient.from_service_account_json(credentials_json)
        else: # В противном случае используется конфигурация по умолчанию
            client = speech.SpeechClient()

        flac_data = audio_data.get_flac_data(
            convert_rate=None if 8000 <= audio_data.sample_rate <= 48000 else max(8000, min(audio_data.sample_rate, 48000)),  # частота дискретизации аудио должна быть от 8 кГц до 48 кГц включительно - ограничиваем частоту дискретизации в этом диапазоне
            convert_width=2  # аудиосемплы должны быть 16-битными
        )
        audio = speech.RecognitionAudio(content=flac_data) # Создание объекта аудио для API

        config_dict = { # Использование словаря для сборки конфигурации
            'encoding': speech.RecognitionConfig.AudioEncoding.FLAC,
            'sample_rate_hertz': audio_data.sample_rate,
            'language_code': language
        }
        if preferred_phrases is not None: # Добавление предпочтительных фраз, если они есть
            config_dict['speech_contexts'] = [speech.SpeechContext( # Использование speech_contexts вместо speechContexts
                phrases=list(preferred_phrases) # Убедимся, что это список
            )]
        if show_all: # Дополнительные опции, если нужен полный вывод
            config_dict['enable_word_time_offsets'] = True

        opts = {} # Опции для запроса
        if self.operation_timeout and socket.getdefaulttimeout() is None: # Установка таймаута операции
            opts['timeout'] = self.operation_timeout

        config = speech.RecognitionConfig(**config_dict) # Создание объекта конфигурации

        try:
            response = client.recognize(config=config, audio=audio, **opts) # Выполнение запроса на распознавание
        except GoogleAPICallError as e: # Обработка ошибок API Google
            raise RequestError(str(e)) # Преобразование исключения в RequestError
        except URLError as e: # Обработка ошибок URL
            raise RequestError("Ошибка подключения для распознавания: {0}".format(e.reason))

        if show_all: return response # Возврат полного ответа, если show_all=True
        if not response.results: raise UnknownValueError() # Исключение, если результатов нет

        transcript = ''.join(result.alternatives[0].transcript.strip() + ' ' for result in response.results if result.alternatives)
        return transcript.strip() # Возврат объединенной транскрипции

    def recognize_wit(self, audio_data, key, show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Wit.ai API.

        Ключ API Wit.ai указывается параметром ``key``. К сожалению, они недоступны без `регистрации учетной записи <https://wit.ai/>`__ и создания приложения. Вам потребуется добавить хотя бы одно намерение в приложение, прежде чем вы сможете увидеть ключ API, хотя фактические настройки намерения не имеют значения.

        Чтобы получить ключ API для приложения Wit.ai, перейдите на страницу обзора приложения, перейдите в раздел «Сделать запрос API» и найдите что-то вроде ``Authorization: Bearer XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX``; ``XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`` — это ключ API. Ключи API Wit.ai представляют собой 32-символьные буквенно-цифровые строки в верхнем регистре.

        Язык распознавания настраивается в настройках приложения Wit.ai.

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно false (по умолчанию). В противном случае возвращает `необработанный ответ API <https://wit.ai/docs/http/20141022#get-intent-via-text-link>`__ в виде словаря JSON.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если операция распознавания речи не удалась, если ключ недействителен или если нет подключения к Интернету.
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(key, str), "``key`` должен быть строкой"

        wav_data = audio_data.get_wav_data(
            convert_rate=None if audio_data.sample_rate >= 8000 else 8000,  # аудиосемплы должны быть не менее 8 кГц
            convert_width=2  # аудиосемплы должны быть 16-битными
        )
        url = "https://api.wit.ai/speech?v=20170307"
        request = Request(url, data=wav_data, headers={"Authorization": "Bearer {}".format(key), "Content-Type": "audio/wav"})
        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("Запрос на распознавание не удался: {}".format(e.reason))
        except URLError as e:
            raise RequestError("Ошибка подключения для распознавания: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)

        # возврат результатов
        if show_all: return result
        if "_text" not in result or result["_text"] is None: raise UnknownValueError()
        return result["_text"]

    def recognize_azure(self, audio_data, key, language="en-US", profanity="masked", location="westus", show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Microsoft Azure Speech API.

        Ключ API Microsoft Azure Speech указывается параметром ``key``. К сожалению, они недоступны без `регистрации учетной записи <https://azure.microsoft.com/en-ca/pricing/details/cognitive-services/speech-api/>`__ в Microsoft Azure.

        Чтобы получить ключ API, перейдите на страницу `Ресурсы портала Microsoft Azure <https://portal.azure.com/>`__, перейдите в «Все ресурсы» > «Добавить» > «Просмотреть все» > Найдите «Речь» > «Создать» и заполните форму для создания ресурса «Речь». На открывшейся странице (которая также доступна со страницы «Все ресурсы» на портале Azure) перейдите на страницу «Показать ключи доступа», где будут два ключа API, любой из которых можно использовать для параметра `key`. Ключи API Microsoft Azure Speech представляют собой 32-символьные шестнадцатеричные строки в нижнем регистре.

        Язык распознавания определяется параметром ``language``, тегом языка BCP-47, например, ``"en-US"`` (американский английский) или ``"fr-FR"`` (международный французский), по умолчанию используется американский английский. Список поддерживаемых значений языка можно найти в `документации API <https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition#recognition-language>`__ в разделе «Интерактивный режим и режим диктовки».

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно false (по умолчанию). В противном случае возвращает `необработанный ответ API <https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition#sample-responses>`__ в виде словаря JSON.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если операция распознавания речи не удалась, если ключ недействителен или если нет подключения к Интернету.
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(key, str), "``key`` должен быть строкой"
        # assert isinstance(result_format, str), "``format`` должен быть строкой" # simple|detailed (простой|детальный) - комментарий оставлен для информации
        assert isinstance(language, str), "``language`` должен быть строкой"

        result_format = 'detailed' # Формат результата
        access_token, expire_time = getattr(self, "azure_cached_access_token", None), getattr(self, "azure_cached_access_token_expiry", None)
        allow_caching = True # Разрешить кэширование токена
        try:
            from time import (
                monotonic,  # нам нужно монотонное время, чтобы избежать влияния изменений системных часов, но это доступно только в Python 3.3+
            )
        except ImportError: # pragma: no cover
            expire_time = None  # монотонное время недоступно, не кэшируем токены доступа
            allow_caching = False  # не разрешаем кэширование, так как монотонное время недоступно
        if expire_time is None or monotonic() > expire_time:  # кэширование не включено, первый запрос учетных данных или срок действия токена доступа из предыдущего истек
            # получение токена доступа с использованием OAuth
            credential_url = "https://" + location + ".api.cognitive.microsoft.com/sts/v1.0/issueToken"
            credential_request = Request(credential_url, data=b"", headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Content-Length": "0",
                "Ocp-Apim-Subscription-Key": key,
            })

            if allow_caching:
                start_time = monotonic()

            try:
                credential_response = urlopen(credential_request, timeout=60)  # ответ на запрос учетных данных может занять больше времени, используем больший тайм-аут вместо стандартного
            except HTTPError as e:
                raise RequestError("Запрос учетных данных не удался: {}".format(e.reason))
            except URLError as e:
                raise RequestError("Ошибка подключения для учетных данных: {}".format(e.reason))
            access_token = credential_response.read().decode("utf-8")

            if allow_caching:
                # сохранение токена на время его действия
                self.azure_cached_access_token = access_token
                self.azure_cached_access_token_expiry = start_time + 600  # согласно https://docs.microsoft.com/en-us/azure/cognitive-services/Speech-Service/rest-apis#authentication, срок действия токена истекает ровно через 10 минут

        wav_data = audio_data.get_wav_data(
            convert_rate=16000,  # аудиосемплы должны быть 8 кГц или 16 кГц
            convert_width=2  # аудиосемплы должны быть 16-битными
        )

        url = "https://" + location + ".stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?{}".format(urlencode({
            "language": language,
            "format": result_format,
            "profanity": profanity # Фильтрация ненормативной лексики
        }))

        if sys.version_info >= (3, 6):  # запросы с фрагментированной передачей поддерживаются в стандартной библиотеке только начиная с Python 3.6+, используем их, если возможно
            request = Request(url, data=io.BytesIO(wav_data), headers={
                "Authorization": "Bearer {}".format(access_token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })
        else:  # возвращаемся к ручному форматированию тела POST как фрагментированного запроса
            ascii_hex_data_length = "{:X}".format(len(wav_data)).encode("utf-8")
            chunked_transfer_encoding_data = ascii_hex_data_length + b"\r\n" + wav_data + b"\r\n0\r\n\r\n"
            request = Request(url, data=chunked_transfer_encoding_data, headers={
                "Authorization": "Bearer {}".format(access_token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })

        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("Запрос на распознавание не удался: {}".format(e.reason))
        except URLError as e:
            raise RequestError("Ошибка подключения для распознавания: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)

        # возврат результатов
        if show_all:
            return result
        if "RecognitionStatus" not in result or result["RecognitionStatus"] != "Success" or "NBest" not in result: # Проверка успешности распознавания
            raise UnknownValueError()
        return result['NBest'][0]["Display"], result['NBest'][0]["Confidence"] # Возврат текста и уверенности

    def recognize_bing(self, audio_data, key, language="en-US", show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Microsoft Bing Speech API.
        (Примечание: Bing Speech API был заменен Azure Speech Services. Этот метод может быть устаревшим.)

        Ключ API Microsoft Bing Speech указывается параметром ``key``. К сожалению, они недоступны без `регистрации учетной записи <https://azure.microsoft.com/en-ca/pricing/details/cognitive-services/speech-api/>`__ в Microsoft Azure.

        Чтобы получить ключ API, перейдите на страницу `Ресурсы портала Microsoft Azure <https://portal.azure.com/>`__, перейдите в «Все ресурсы» > «Добавить» > «Просмотреть все» > Найдите «Bing Speech API» > «Создать» и заполните форму для создания ресурса «Bing Speech API». На открывшейся странице (которая также доступна со страницы «Все ресурсы» на портале Azure) перейдите на страницу «Показать ключи доступа», где будут два ключа API, любой из которых можно использовать для параметра `key`. Ключи API Microsoft Bing Speech представляют собой 32-символьные шестнадцатеричные строки в нижнем регистре.

        Язык распознавания определяется параметром ``language``, тегом языка BCP-47, например, ``"en-US"`` (американский английский) или ``"fr-FR"`` (международный французский), по умолчанию используется американский английский. Список поддерживаемых значений языка можно найти в `документации API <https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition#recognition-language>`__ в разделе «Интерактивный режим и режим диктовки».

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно false (по умолчанию). В противном случае возвращает `необработанный ответ API <https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition#sample-responses>`__ в виде словаря JSON.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если операция распознавания речи не удалась, если ключ недействителен или если нет подключения к Интернету.
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(key, str), "``key`` должен быть строкой"
        assert isinstance(language, str), "``language`` должен быть строкой"

        access_token, expire_time = getattr(self, "bing_cached_access_token", None), getattr(self, "bing_cached_access_token_expiry", None)
        allow_caching = True
        try:
            from time import (
                monotonic,  # нам нужно монотонное время, чтобы избежать влияния изменений системных часов, но это доступно только в Python 3.3+
            )
        except ImportError: # pragma: no cover
            expire_time = None  # монотонное время недоступно, не кэшируем токены доступа
            allow_caching = False  # не разрешаем кэширование, так как монотонное время недоступно
        if expire_time is None or monotonic() > expire_time:  # кэширование не включено, первый запрос учетных данных или срок действия токена доступа из предыдущего истек
            # получение токена доступа с использованием OAuth
            credential_url = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken" # URL для получения токена (может быть устаревшим для Bing)
            credential_request = Request(credential_url, data=b"", headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Content-Length": "0",
                "Ocp-Apim-Subscription-Key": key,
            })

            if allow_caching:
                start_time = monotonic()

            try:
                credential_response = urlopen(credential_request, timeout=60)
            except HTTPError as e:
                raise RequestError("Запрос учетных данных не удался: {}".format(e.reason))
            except URLError as e:
                raise RequestError("Ошибка подключения для учетных данных: {}".format(e.reason))
            access_token = credential_response.read().decode("utf-8")

            if allow_caching:
                # сохранение токена на время его действия
                self.bing_cached_access_token = access_token
                self.bing_cached_access_token_expiry = start_time + 600  # согласно https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition, срок действия токена истекает ровно через 10 минут

        wav_data = audio_data.get_wav_data(
            convert_rate=16000,
            convert_width=2
        )

        url = "https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1?{}".format(urlencode({
            "language": language,
            "locale": language, # Локаль
            "requestid": uuid.uuid4(), # Уникальный ID запроса
        }))

        if sys.version_info >= (3, 6):
            request = Request(url, data=io.BytesIO(wav_data), headers={
                "Authorization": "Bearer {}".format(access_token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })
        else: # pragma: no cover
            ascii_hex_data_length = "{:X}".format(len(wav_data)).encode("utf-8")
            chunked_transfer_encoding_data = ascii_hex_data_length + b"\r\n" + wav_data + b"\r\n0\r\n\r\n"
            request = Request(url, data=chunked_transfer_encoding_data, headers={
                "Authorization": "Bearer {}".format(access_token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })

        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("Запрос на распознавание не удался: {}".format(e.reason))
        except URLError as e:
            raise RequestError("Ошибка подключения для распознавания: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)

        # возврат результатов
        if show_all: return result
        if "RecognitionStatus" not in result or result["RecognitionStatus"] != "Success" or "DisplayText" not in result: raise UnknownValueError()
        return result["DisplayText"]

    def recognize_lex(self, audio_data, bot_name, bot_alias, user_id, content_type="audio/l16; rate=16000; channels=1", access_key_id=None, secret_access_key=None, region=None):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Amazon Lex API.

        Если ``access_key_id`` или ``secret_access_key`` не установлены, он будет проходить по списку в ссылке ниже:
        http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(bot_name, str), "``bot_name`` должен быть строкой"
        assert isinstance(bot_alias, str), "``bot_alias`` должен быть строкой"
        assert isinstance(user_id, str), "``user_id`` должен быть строкой"
        assert isinstance(content_type, str), "``content_type`` должен быть строкой"
        assert access_key_id is None or isinstance(access_key_id, str), "``access_key_id`` должен быть строкой"
        assert secret_access_key is None or isinstance(secret_access_key, str), "``secret_access_key`` должен быть строкой"
        assert region is None or isinstance(region, str), "``region`` должен быть строкой"

        try:
            import boto3 # Клиент AWS SDK для Python
        except ImportError: # pragma: no cover
            raise RequestError("Отсутствует модуль boto3: убедитесь, что boto3 настроен правильно.")

        # Создание клиента Lex Runtime
        client = boto3.client('lex-runtime', aws_access_key_id=access_key_id,
                              aws_secret_access_key=secret_access_key,
                              region_name=region)

        raw_data = audio_data.get_raw_data(
            convert_rate=16000, convert_width=2 # Преобразование аудио к нужному формату
        )

        accept = "text/plain; charset=utf-8" # Ожидаемый формат ответа
        # Отправка контента в Lex
        response = client.post_content(botName=bot_name, botAlias=bot_alias, userId=user_id, contentType=content_type, accept=accept, inputStream=raw_data)

        return response["inputTranscript"] # Возврат транскрипции из ответа

    def recognize_houndify(self, audio_data, client_id, client_key, show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Houndify API.

        ID клиента Houndify и ключ клиента указываются параметрами ``client_id`` и ``client_key`` соответственно. К сожалению, они недоступны без `регистрации учетной записи <https://www.houndify.com/signup>`__. После входа в `панель управления <https://www.houndify.com/dashboard>`__ вам нужно будет выбрать «Зарегистрировать нового клиента» и заполнить форму соответствующим образом. На странице «Включить домены» включите домен «Только преобразование речи в текст», а затем выберите «Сохранить и продолжить».

        Чтобы получить ID клиента и ключ клиента для клиента Houndify, перейдите в `панель управления <https://www.houndify.com/dashboard>`__ и выберите ссылку «Просмотреть детали» клиента. На открывшейся странице будут видны ID клиента и ключ клиента. ID клиентов и ключи клиентов являются строками в кодировке Base64.

        В настоящее время в качестве языка распознавания поддерживается только английский.

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно false (по умолчанию). В противном случае возвращает необработанный ответ API в виде словаря JSON.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если операция распознавания речи не удалась, если ключ недействителен или если нет подключения к Интернету.
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(client_id, str), "``client_id`` должен быть строкой"
        assert isinstance(client_key, str), "``client_key`` должен быть строкой"

        wav_data = audio_data.get_wav_data(
            convert_rate=None if audio_data.sample_rate in [8000, 16000] else 16000,  # аудиосемплы должны быть 8 кГц или 16 кГц
            convert_width=2  # аудиосемплы должны быть 16-битными
        )
        url = "https://api.houndify.com/v1/audio" # URL API Houndify
        user_id, request_id = str(uuid.uuid4()), str(uuid.uuid4()) # Генерация уникальных ID
        request_time = str(int(time.time())) # Текущее время для подписи
        # Создание подписи запроса
        request_signature = base64.urlsafe_b64encode(
            hmac.new(
                base64.urlsafe_b64decode(client_key),
                user_id.encode("utf-8") + b";" + request_id.encode("utf-8") + request_time.encode("utf-8"),
                hashlib.sha256
            ).digest()  # получение HMAC-дайджеста в виде байтов
        ).decode("utf-8")
        request = Request(url, data=wav_data, headers={ # Формирование запроса
            "Content-Type": "application/json", # Неверный Content-Type для аудио, должен быть audio/wav. Однако, API может ожидать JSON для метаданных в некоторых случаях.
            "Hound-Request-Info": json.dumps({"ClientID": client_id, "UserID": user_id}),
            "Hound-Request-Authentication": "{};{}".format(user_id, request_id),
            "Hound-Client-Authentication": "{};{};{}".format(client_id, request_time, request_signature)
        })
        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("Запрос на распознавание не удался: {}".format(e.reason))
        except URLError as e:
            raise RequestError("Ошибка подключения для распознавания: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)

        # возврат результатов
        if show_all: return result
        if "Disambiguation" not in result or result["Disambiguation"] is None or not result["Disambiguation"]["ChoiceData"]: # Более строгая проверка
            raise UnknownValueError()
        # Возвращаем транскрипцию и оценку уверенности из первого варианта
        return result['Disambiguation']['ChoiceData'][0]['Transcription'], result['Disambiguation']['ChoiceData'][0]['ConfidenceScore']

    def recognize_amazon(self, audio_data, bucket_name=None, access_key_id=None, secret_access_key=None, region=None, job_name=None, file_key=None):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Amazon Transcribe.
        https://aws.amazon.com/transcribe/
        Если ``access_key_id`` или ``secret_access_key`` не установлены, он будет проходить по списку в ссылке ниже:
        http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials
        """
        assert access_key_id is None or isinstance(access_key_id, str), "``access_key_id`` должен быть строкой"
        assert secret_access_key is None or isinstance(secret_access_key, str), "``secret_access_key`` должен быть строкой"
        assert region is None or isinstance(region, str), "``region`` должен быть строкой"
        import multiprocessing # Для получения ID процесса
        import traceback # Для печати стека вызовов
        import uuid # Для генерации уникальных имен

        from botocore.exceptions import ClientError # Исключения Boto3
        proc = multiprocessing.current_process()

        check_existing = audio_data is None and job_name # Проверка существующей задачи

        bucket_name = bucket_name or ('%s-%s' % (str(uuid.uuid4()), proc.pid)) # Имя бакета S3
        job_name = job_name or ('%s-%s' % (str(uuid.uuid4()), proc.pid)) # Имя задачи транскрибации

        try:
            import boto3
        except ImportError: # pragma: no cover
            raise RequestError("Отсутствует модуль boto3: убедитесь, что boto3 настроен правильно.")

        # Клиент Transcribe
        transcribe = boto3.client(
            'transcribe',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region)

        # Клиент S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region)

        # Сессия Boto3
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )

        # Загрузка аудиоданных в S3.
        filename = '%s.wav' % job_name
        try:
            # Создание бакета часто завершается неудачей, даже если бакет существует.
            # print('Попытка создать бакет %s...' % bucket_name)
            s3.create_bucket(Bucket=bucket_name)
        except ClientError as exc:
            print('Ошибка создания бакета %s: %s' % (bucket_name, exc))
        s3res = session.resource('s3')
        if audio_data is not None: # Если предоставлены аудиоданные
            print('Загрузка аудиоданных...')
            wav_data = audio_data.get_wav_data()
            s3.put_object(Bucket=bucket_name, Key=filename, Body=wav_data) # Загрузка объекта
            object_acl = s3res.ObjectAcl(bucket_name, filename)
            object_acl.put(ACL='public-read') # Установка публичного доступа (может быть небезопасно)
        else: # Если аудиоданные не предоставлены (проверяем существующую задачу)
            print('Пропуск загрузки аудио.')
        job_uri = 'https://%s.s3.amazonaws.com/%s' % (bucket_name, filename) # URI задачи

        if check_existing: # Если проверяем существующую задачу

            # Ожидание завершения задачи.
            try:
                status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            except ClientError as exc:
                print('!' * 80)
                print('Ошибка получения задачи:', exc.response)
                if exc.response['Error']['Code'] == 'BadRequestException' and "The requested job couldn't be found" in str(exc):
                    # Какая-то ошибка привела к тому, что записанная нами задача не существует на AWS.
                    # Вероятно, нас прервали сразу после получения и удаления задачи, но до записи транскрипции.
                    # Сбросить и повторить попытку позже.
                    exc_new = TranscriptionNotReady("Задача транскрипции не найдена на AWS.") # Используем русское сообщение
                    exc_new.job_name = None
                    exc_new.file_key = None
                    raise exc_new
                else:
                    # Произошла какая-то другая ошибка, поэтому повторно вызываем.
                    raise

            job = status['TranscriptionJob']
            if job['TranscriptionJobStatus'] in ['COMPLETED'] and 'TranscriptFileUri' in job['Transcript']:

                # Получение JSON транскрипции, содержащего транскрипт.
                transcript_uri = job['Transcript']['TranscriptFileUri']
                import json
                import urllib.request
                with urllib.request.urlopen(transcript_uri) as json_data:
                    d = json.load(json_data)
                    confidences = []
                    for item in d['results']['items']:
                        confidences.append(float(item['alternatives'][0]['confidence']))
                    confidence = 0.5 # Уверенность по умолчанию
                    if confidences:
                        confidence = sum(confidences) / float(len(confidences)) # Средняя уверенность
                    transcript = d['results']['transcripts'][0]['transcript'] # Текст транскрипции

                    # Удаление задачи.
                    try:
                        transcribe.delete_transcription_job(TranscriptionJobName=job_name)  # очистка
                    except Exception as exc_clean:
                        print('Предупреждение, не удалось очистить транскрипцию: %s' % exc_clean)
                        traceback.print_exc()

                    # Удаление файла S3.
                    s3.delete_object(Bucket=bucket_name, Key=filename)

                    return transcript, confidence
            elif job['TranscriptionJobStatus'] in ['FAILED']: # Если задача не удалась

                # Удаление задачи.
                try:
                    transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                except Exception as exc_clean_fail:
                    print('Предупреждение, не удалось очистить транскрипцию (неудачную): %s' % exc_clean_fail)
                    traceback.print_exc()

                # Удаление файла S3.
                s3.delete_object(Bucket=bucket_name, Key=filename)

                exc_failed = TranscriptionFailed("Задача транскрипции не удалась.") # Используем русское сообщение
                exc_failed.job_name = None
                exc_failed.file_key = None
                raise exc_failed
            else: # Если задача еще не завершена
                # Продолжаем ждать.
                print('Продолжаем ждать.')
                exc_not_ready = TranscriptionNotReady("Задача транскрипции еще не готова.") # Используем русское сообщение
                exc_not_ready.job_name = job_name
                exc_not_ready.file_key = None
                raise exc_not_ready

        else: # Если запускаем новую задачу

            # Запуск задачи транскрибации.
            try:
                transcribe.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': job_uri},
                    MediaFormat='wav',
                    LanguageCode='en-US' # Языковой код (можно сделать параметром)
                )
                exc_new_job = TranscriptionNotReady("Задача транскрипции запущена, ожидайте результатов.") # Используем русское сообщение
                exc_new_job.job_name = job_name
                exc_new_job.file_key = None
                raise exc_new_job
            except ClientError as exc:
                print('!' * 80)
                print('Ошибка запуска задачи:', exc.response)
                if exc.response['Error']['Code'] == 'LimitExceededException':
                    # Не удалось запустить задачу. Отменяем все.
                    s3.delete_object(Bucket=bucket_name, Key=filename)
                    exc_limit = TranscriptionNotReady("Не удалось запустить задачу транскрипции из-за превышения лимита.") # Используем русское сообщение
                    exc_limit.job_name = None
                    exc_limit.file_key = None
                    raise exc_limit
                else:
                    # Произошла какая-то другая ошибка, поэтому повторно вызываем.
                    raise

    def recognize_assemblyai(self, audio_data, api_token, job_name=None, **kwargs):
        """
        Обертка для сервиса STT AssemblyAI.
        https://www.assemblyai.com/
        """

        def read_file(filename, chunk_size=5242880):
            """Читает файл по частям."""
            with open(filename, 'rb') as _file:
                while True:
                    data = _file.read(chunk_size)
                    if not data:
                        break
                    yield data

        check_existing = audio_data is None and job_name # Проверка существующей задачи
        if check_existing:
            # Запрос статуса.
            transcription_id = job_name # Используем правильное имя переменной
            endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"
            headers = {
                "authorization": api_token,
            }
            response = requests.get(endpoint, headers=headers) # Используем requests, если он импортирован
            data = response.json()
            status = data['status']

            if status == 'error':
                # Обработка ошибки.
                exc_err = TranscriptionFailed("Ошибка при транскрибации AssemblyAI.") # Используем русское сообщение
                exc_err.job_name = None
                exc_err.file_key = None
                raise exc_err
                # Обработка успеха.
            elif status == 'completed':
                confidence = data['confidence']
                text = data['text']
                return text, confidence

            # В противном случае продолжаем ждать.
            print('Продолжаем ждать.')
            exc_not_rdy = TranscriptionNotReady("Транскрипция AssemblyAI еще не готова.") # Используем русское сообщение
            exc_not_rdy.job_name = job_name
            exc_not_rdy.file_key = None
            raise exc_not_rdy
        else:
            # Загрузка файла.
            headers = {'authorization': api_token}
            # `audio_data` здесь должен быть путем к файлу, а не объектом AudioData,
            # если используется `read_file`. Предполагаем, что это так.
            if not isinstance(audio_data, str) or not os.path.exists(audio_data):
                 raise ValueError("Для AssemblyAI `audio_data` должен быть путем к существующему файлу при отсутствии `job_name`.")

            response = requests.post('https://api.assemblyai.com/v2/upload',
                                     headers=headers,
                                     data=read_file(audio_data))
            upload_url = response.json()['upload_url']

            # Постановка файла в очередь на транскрибацию.
            endpoint = "https://api.assemblyai.com/v2/transcript"
            json_payload = {"audio_url": upload_url, **kwargs} # Передаем kwargs в тело запроса
            headers = {
                "authorization": api_token,
                "content-type": "application/json"
            }
            response = requests.post(endpoint, json=json_payload, headers=headers)
            data = response.json()
            transcription_id_new = data['id'] # Используем новое имя переменной
            exc_queued = TranscriptionNotReady("Файл поставлен в очередь на транскрибацию AssemblyAI.") # Используем русское сообщение
            exc_queued.job_name = transcription_id_new
            exc_queued.file_key = None
            raise exc_queued

    def recognize_ibm(self, audio_data, key, language="en-US", show_all=False):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя IBM Speech to Text API.

        Имя пользователя и пароль IBM Speech to Text указываются параметрами ``username`` и ``password`` соответственно. К сожалению, они недоступны без `регистрации учетной записи <https://console.ng.bluemix.net/registration/>`__. После входа в консоль Bluemix следуйте инструкциям по `созданию экземпляра службы IBM Watson <https://www.ibm.com/watson/developercloud/doc/getting_started/gs-credentials.shtml>`__, где службой Watson является «Speech To Text». Имена пользователей IBM Speech to Text представляют собой строки вида XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX, а пароли — буквенно-цифровые строки в смешанном регистре.
        (Примечание: IBM Watson Speech to Text теперь использует API-ключи вместо имени пользователя/пароля. Параметр `key` должен быть API-ключом.)

        Язык распознавания определяется параметром ``language``, тегом языка RFC5646 с диалектом, например, ``"en-US"`` (американский английский) или ``"zh-CN"`` (мандаринский китайский), по умолчанию используется американский английский. Поддерживаемые значения языка перечислены в параметре ``model`` `документации API распознавания аудио <https://www.ibm.com/watson/developercloud/speech-to-text/api/v1/#sessionless_methods>`__ в виде ``LANGUAGE_BroadbandModel``, где ``LANGUAGE`` — это значение языка.

        Возвращает наиболее вероятную транскрипцию, если ``show_all`` равно false (по умолчанию). В противном случае возвращает `необработанный ответ API <https://www.ibm.com/watson/developercloud/speech-to-text/api/v1/#sessionless_methods>`__ в виде словаря JSON.

        Вызывает исключение ``speech_recognition.UnknownValueError``, если речь неразборчива. Вызывает исключение ``speech_recognition.RequestError``, если операция распознавания речи не удалась, если ключ недействителен или если нет подключения к Интернету.
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(key, str), "``key`` (API-ключ) должен быть строкой"

        flac_data = audio_data.get_flac_data(
            convert_rate=None if audio_data.sample_rate >= 16000 else 16000,  # аудиосемплы должны быть не менее 16 кГц
            convert_width=None if audio_data.sample_width >= 2 else 2  # аудиосемплы должны быть не менее 16-битными
        )
        url = "https://gateway-wdc.watsonplatform.net/speech-to-text/api/v1/recognize" # URL может отличаться в зависимости от региона
        request = Request(url, data=flac_data, headers={
            "Content-Type": "audio/x-flac", # Тип контента
        })
        request.get_method = lambda: 'POST' # Установка метода POST
        username = 'apikey' # Для IAM аутентификации
        password = key # API-ключ используется как пароль
        authorization_value = base64.standard_b64encode("{}:{}".format(username, password).encode("utf-8")).decode("utf-8")
        request.add_header("Authorization", "Basic {}".format(authorization_value)) # Добавление заголовка авторизации
        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("Запрос на распознавание не удался: {}".format(e.reason))
        except URLError as e:
            raise RequestError("Ошибка подключения для распознавания: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)

        # возврат результатов
        if show_all:
            return result
        if "results" not in result or len(result["results"]) < 1 or "alternatives" not in result["results"][0]:
            raise UnknownValueError()

        transcription = []
        confidence = None # Уверенность
        for utterance in result["results"]:
            if "alternatives" not in utterance: raise UnknownValueError()
            for hypothesis in utterance["alternatives"]:
                if "transcript" in hypothesis:
                    transcription.append(hypothesis["transcript"])
                    if "confidence" in hypothesis: # Уверенность может отсутствовать
                        confidence = hypothesis["confidence"]
                    break # Берем первую гипотезу
        return "\n".join(transcription), confidence # Возвращаем транскрипцию и уверенность

    lasttfgraph = '' # Последний использованный граф TensorFlow
    tflabels = None # Метки TensorFlow

    def recognize_tensorflow(self, audio_data, tensor_graph='tensorflow-data/conv_actions_frozen.pb', tensor_label='tensorflow-data/conv_actions_labels.txt'):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя TensorFlow.
        (Этот метод, вероятно, устарел и предназначен для конкретной задачи распознавания команд.)

        Путь к тензору, загруженному из ``tensor_graph``. Вы можете скачать модель здесь: http://download.tensorflow.org/models/speech_commands_v0.01.zip

        Путь к файлу меток тензора, загруженному из ``tensor_label``.
        """
        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        assert isinstance(tensor_graph, str), "``tensor_graph`` должен быть строкой"
        assert isinstance(tensor_label, str), "``tensor_label`` должен быть строкой"

        try:
            import tensorflow as tf
        except ImportError: # pragma: no cover
            raise RequestError("Отсутствует модуль tensorflow: убедитесь, что tensorflow настроен правильно.")

        if not (tensor_graph == self.lasttfgraph): # Если граф изменился, загружаем новый
            self.lasttfgraph = tensor_graph

            # загрузка графа
            with tf.io.gfile.GFile(tensor_graph, 'rb') as f: # Используем tf.io.gfile.GFile для совместимости
                graph_def = tf.compat.v1.GraphDef() # Используем tf.compat.v1.GraphDef
                graph_def.ParseFromString(f.read())
                tf.import_graph_def(graph_def, name='')
            # загрузка меток
            self.tflabels = [line.rstrip() for line in tf.io.gfile.GFile(tensor_label)]

        wav_data = audio_data.get_wav_data(
            convert_rate=16000, convert_width=2 # Преобразование аудио
        )

        with tf.compat.v1.Session() as sess: # Используем tf.compat.v1.Session
            input_layer_name = 'wav_data:0' # Имя входного слоя
            output_layer_name = 'labels_softmax:0' # Имя выходного слоя
            softmax_tensor = sess.graph.get_tensor_by_name(output_layer_name)
            predictions, = sess.run(softmax_tensor, {input_layer_name: wav_data})

            # Сортировка меток по уверенности
            top_k = predictions.argsort()[-1:][::-1] # Получение индекса наиболее вероятной метки
            for node_id in top_k:
                human_string = self.tflabels[node_id]
                return human_string
        return None # Возвращаем None, если что-то пошло не так

    def recognize_whisper(self, audio_data, model="base", show_dict=False, load_options=None, language=None, translate=False, **transcribe_options):
        """
        Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Whisper.

        Язык распознавания определяется параметром ``language``, полным названием языка в нижнем регистре, например, "english" или "chinese". Полный список языков см. на https://github.com/openai/whisper/blob/main/whisper/tokenizer.py

        Параметр ``model`` может быть любым из tiny, base, small, medium, large, tiny.en, base.en, small.en, medium.en. Подробнее см. на https://github.com/openai/whisper.

        Если ``show_dict`` равно true, возвращает полный ответ словаря от Whisper, включая обнаруженный язык. В противном случае возвращает только транскрипцию.

        Вы можете перевести результат на английский с помощью Whisper, передав ``translate=True``.

        Другие значения передаются напрямую в Whisper. См. https://github.com/openai/whisper/blob/main/whisper/transcribe.py для всех опций.
        """

        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"
        import numpy as np
        import soundfile as sf
        import torch
        import whisper # Импорт OpenAI Whisper

        if load_options or not hasattr(self, "whisper_model") or self.whisper_model.get(model) is None:
            self.whisper_model = getattr(self, "whisper_model", {}) # Инициализация словаря моделей, если его нет
            self.whisper_model[model] = whisper.load_model(model, **(load_options or {})) # Загрузка модели Whisper

        # 16 кГц https://github.com/openai/whisper/blob/28769fcfe50755a817ab922a7bc83483159600a9/whisper/audio.py#L98-L99
        wav_bytes = audio_data.get_wav_data(convert_rate=16000) # Получение WAV-данных с нужной частотой
        wav_stream = io.BytesIO(wav_bytes) # Создание потока байтов
        audio_array, sampling_rate = sf.read(wav_stream) # Чтение аудио из потока
        audio_array = audio_array.astype(np.float32) # Преобразование в float32

        # Транскрибация аудио
        result = self.whisper_model[model].transcribe(
            audio_array,
            language=language,
            task="translate" if translate else None, # Задача: транскрибация или перевод
            fp16=torch.cuda.is_available(), # Использование fp16, если доступно CUDA
            **transcribe_options # Другие опции транскрибации
        )

        if show_dict: # Если нужно вернуть полный словарь
            return result
        else: # Иначе вернуть только текст
            return result["text"]

    def recognize_vosk(self, audio_data, language='en'):
        """Распознает речь с помощью Vosk API."""
        from vosk import KaldiRecognizer, Model # Импорт из Vosk

        assert isinstance(audio_data, AudioData), "Данные должны быть аудиоданными"

        if not hasattr(self, 'vosk_model_map'): # Используем карту для поддержки нескольких языков
            self.vosk_model_map = {}

        if language not in self.vosk_model_map:
            model_path = f"model-{language}" # Предполагаем, что модели хранятся в папках model-en, model-ru и т.д.
            if not os.path.exists(model_path):
                # Это сообщение будет выведено, если модель для указанного языка не найдена.
                # Пользователю нужно будет скачать соответствующую модель.
                return "Пожалуйста, загрузите модель для языка '{}' с https://alphacephei.com/vosk/models и распакуйте как '{}' в текущей папке.".format(language, model_path)
            self.vosk_model_map[language] = Model(model_path)

        rec = KaldiRecognizer(self.vosk_model_map[language], 16000) # Инициализация распознавателя

        rec.AcceptWaveform(audio_data.get_raw_data(convert_rate=16000, convert_width=2)) # Передача аудиоданных
        finalRecognition = json.loads(rec.FinalResult()) # Получение окончательного результата в виде JSON

        return finalRecognition.get("text", "") # Извлечение текста из результата


class PortableNamedTemporaryFile(object):
    """Ограниченная замена для ``tempfile.NamedTemporaryFile``, за исключением того, что, в отличие от ``tempfile.NamedTemporaryFile``, файл можно открыть снова, пока он открыт, даже в Windows."""
    def __init__(self, mode="w+b"):
        self.mode = mode # Режим открытия файла

    def __enter__(self):
        # создание временного файла и его открытие
        file_descriptor, file_path = tempfile.mkstemp()
        self._file = os.fdopen(file_descriptor, self.mode)

        # свойство name является публичным полем
        self.name = file_path
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Закрытие и удаление временного файла при выходе из контекста."""
        self._file.close()
        os.remove(self.name)

    def write(self, *args, **kwargs):
        """Запись данных в файл."""
        return self._file.write(*args, **kwargs)

    def writelines(self, *args, **kwargs):
        """Запись списка строк в файл."""
        return self._file.writelines(*args, **kwargs)

    def flush(self, *args, **kwargs):
        """Сброс буфера файла."""
        return self._file.flush(*args, **kwargs)


# Во время процесса установки pip выполняется команда 'import speech_recognition' в setup.py.
# В это время зависимости еще не установлены, что приводит к ModuleNotFoundError.
# Это обходной путь для решения этой проблемы.
try:
    from .recognizers import google, whisper
except (ModuleNotFoundError, ImportError): # pragma: no cover
    pass
else: # pragma: no cover
    Recognizer.recognize_google = google.recognize_legacy
    Recognizer.recognize_whisper_api = whisper.recognize_whisper_api


# ===============================
#  заглушки для обратной совместимости
# ===============================

WavFile = AudioFile  # WavFile был переименован в AudioFile в версии 3.4.1


def recognize_api(self, audio_data, client_access_token, language="en", session_id=None, show_all=False):
    """Распознает речь с помощью API.AI (теперь Dialogflow). Этот метод устарел."""
    wav_data = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
    url = "https://api.api.ai/v1/query" # URL API.AI
    while True: # Генерация уникальной границы для multipart/form-data
        boundary = uuid.uuid4().hex
        if boundary.encode("utf-8") not in wav_data: break # Убедиться, что граница не содержится в данных
    if session_id is None: session_id = uuid.uuid4().hex # Генерация ID сессии, если не предоставлен
    # Формирование тела запроса multipart/form-data
    data = b"--" + boundary.encode("utf-8") + b"\r\n" + b"Content-Disposition: form-data; name=\"request\"\r\n" + b"Content-Type: application/json\r\n" + b"\r\n" + b"{\"v\": \"20150910\", \"sessionId\": \"" + session_id.encode("utf-8") + b"\", \"lang\": \"" + language.encode("utf-8") + b"\"}\r\n" + b"--" + boundary.encode("utf-8") + b"\r\n" + b"Content-Disposition: form-data; name=\"voiceData\"; filename=\"audio.wav\"\r\n" + b"Content-Type: audio/wav\r\n" + b"\r\n" + wav_data + b"\r\n" + b"--" + boundary.encode("utf-8") + b"--\r\n"
    request = Request(url, data=data, headers={"Authorization": "Bearer {}".format(client_access_token), "Content-Length": str(len(data)), "Expect": "100-continue", "Content-Type": "multipart/form-data; boundary={}".format(boundary)})
    try: response = urlopen(request, timeout=10) # Установка таймаута в 10 секунд
    except HTTPError as e: raise RequestError("Запрос на распознавание не удался: {}".format(e.reason))
    except URLError as e: raise RequestError("Ошибка подключения для распознавания: {}".format(e.reason))
    response_text = response.read().decode("utf-8")
    result = json.loads(response_text)
    if show_all: return result # Возврат полного результата, если show_all=True
    if "status" not in result or "errorType" not in result["status"] or result["status"]["errorType"] != "success": # Проверка статуса ответа
        raise UnknownValueError()
    return result["result"]["resolvedQuery"] # Возврат распознанного запроса


Recognizer.recognize_api = classmethod(recognize_api)  # Распознавание речи API.AI устарело/не рекомендуется с версии 3.5.0 и в настоящее время доступно только для платных планов
