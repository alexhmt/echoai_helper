# src/AudioRecorder.py

import src.custom_speech_recognition as sr
import pyaudiowpatch as pyaudio
from datetime import datetime

RECORD_TIMEOUT = 0.6  # Таймаут записи
ENERGY_THRESHOLD = 100  # Порог энергии
DYNAMIC_ENERGY_THRESHOLD = False # Динамический порог энергии выключен
#DYNAMIC_ENERGY_THRESHOLD = True # Динамический порог энергии включен

class BaseRecorder:
    """Базовый класс для записи аудио."""
    def __init__(self, source, source_name):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("Аудиоисточник не может быть None")

        self.source = source
        self.source_name = source_name # Имя источника (например, "You" или "Speaker")

    def adjust_for_noise(self, device_name, msg):
        """Регулирует распознаватель с учетом окружающего шума."""
        print(f"[ИНФО] Регулировка для окружающего шума с {device_name}. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[ИНФО] Регулировка окружающего шума для {device_name} завершена.")

    def record_into_queue(self, audio_queue):
        """Записывает аудио в очередь."""
        def record_callback(_, audio:sr.AudioData) -> None:
            # Обратный вызов, вызываемый при записи аудиоданных
            data = audio.get_raw_data()
            audio_queue.put((self.source_name, data, datetime.utcnow()))

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT)

class DefaultMicRecorder(BaseRecorder):
    """Класс для записи с микрофона по умолчанию."""
    def __init__(self):
        super().__init__(source=sr.Microphone(sample_rate=16000), source_name="You") # "You" можно оставить или перевести как "Вы"
        self.adjust_for_noise("микрофона по умолчанию", "Пожалуйста, пошумите немного в микрофон по умолчанию...")

class DefaultSpeakerRecorder(BaseRecorder):
    """Класс для записи с динамиков по умолчанию."""
    def __init__(self):
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            # Проверка, является ли устройство loopback
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    # Попытка найти соответствующее loopback устройство
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    # Сообщение об ошибке, если loopback устройство не найдено
                    print("[ОШИБКА] Loopback-устройство не найдено.")
        
        source = sr.Microphone(speaker=True,
                               device_index= default_speakers["index"],
                               sample_rate=int(default_speakers["defaultSampleRate"]),
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16), # Размер семпла для формата paInt16
                               channels=default_speakers["maxInputChannels"])
        super().__init__(source=source, source_name="Speaker") # "Speaker" можно оставить или перевести как "Динамик"
        self.adjust_for_noise("динамиков по умолчанию", "Пожалуйста, воспроизведите какой-нибудь звук через динамики по умолчанию...")