# src/TranscriberModels.py

import openai
import yaml
#import whisper # Закомментированный импорт whisper
#from faster_whisper import WhisperModel # Закомментированный импорт faster_whisper
import os
import torch
from src.asr.asr_factory import ASRFactory
from src.asr.asr_interface import ASRInterface
from .config import PathConfig


def get_model(use_api: bool):
    """
    Возвращает экземпляр транскрибатора в зависимости от флага use_api.

    Args:
        use_api (bool): Если True, возвращает APIWhisperTranscriber, иначе FunASRTranscriber.
    
    Returns:
        Union[APIWhisperTranscriber, FunASRTranscriber]: Экземпляр транскрибатора.
    """
    if use_api:
        return APIWhisperTranscriber()
    else:
        return FunASRTranscriber()
        #return WhisperTranscriber() # Закомментированный возврат WhisperTranscriber

class FunASRTranscriber:
    """Класс для транскрибации аудио с использованием FunASR."""
    def __init__(self):
        #self.audio_model = whisper.load_model(os.path.join(os.getcwd(), 'small.pt')) # Загрузка модели whisper (закомментировано)
        with open(f"{PathConfig.get_project_root()}/conf.yaml", "rb") as f:
            self.config = yaml.safe_load(f) # Загрузка конфигурации

        asr_model = "FunASR" # Используемая модель ASR
        asr_config = self.config.get(asr_model, {}) # Получение конфигурации для модели

        self.audio_model = ASRFactory.get_asr_system(asr_model, **asr_config) # Инициализация системы ASR

        print(f"[ИНФО] FunASR использует GPU: " + str(torch.cuda.is_available())) # Проверка доступности GPU

    def init_asr(self) -> ASRInterface:
        """Инициализирует и возвращает систему ASR на основе конфигурации."""
        asr_model = self.config.get("ASR_MODEL") # Получение имени модели ASR из конфигурации
        asr_config = self.config.get(asr_model, {}) # Получение конфигурации для этой модели

        asr = ASRFactory.get_asr_system(asr_model, **asr_config) # Создание экземпляра системы ASR
        return asr

    def get_transcription(self, wav_file_path: str) -> str:
        """
        Получает транскрипцию для указанного WAV-файла.

        Args:
            wav_file_path (str): Путь к WAV-файлу.

        Returns:
            str: Транскрибированный текст или пустая строка в случае ошибки.
        """
        try:
            #with open(wav_file_path, "rb") as audio_file: # Открытие аудиофайла (закомментировано)
            #    self.received_data_buffer = np.array([]) # Инициализация буфера (закомментировано)
            result = self.audio_model.transcribe_wav(wav_file_path) # Транскрибация WAV-файла
            #result = self.audio_model.transcribe(wav_file_path, fp16=torch.cuda.is_available()) # Альтернативный метод транскрибации (закомментировано)
        except Exception as e:
            print(f"Ошибка при транскрибации FunASR: {e}")
            return ''
        return result


class WhisperTranscriber:
    """
    Класс для транскрибации аудио с использованием Whisper.
    (В данный момент этот класс, похоже, не используется активно в пользу FunASR или API)
    """

    # Запуск на GPU с FP16
    #model = WhisperModel(model_size, device="cuda", compute_type="float16")

    # или запуск на GPU с INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # или запуск на CPU с INT8

    def __init__(self):
        #self.audio_model = whisper.load_model(os.path.join(os.getcwd(), 'small.pt')) # Загрузка стандартной модели whisper (закомментировано)

        #model_size = "large-v3-turbo" # Размер модели (закомментировано)
        #model_size = "distil-small.en" # Размер модели (закомментировано)
        model_size = "small.en" # Текущий выбранный размер модели
        # Инициализация модели WhisperModel (предположительно faster_whisper)
        self.audio_model = WhisperModel(model_size, device="cpu",cpu_threads=8, compute_type="int8")

        print(f"[ИНФО] Whisper использует GPU: " + str(torch.cuda.is_available())) # Проверка доступности GPU

    def get_transcription(self, wav_file_path: str) -> str:
        """
        Получает транскрипцию для указанного WAV-файла с использованием Whisper.

        Args:
            wav_file_path (str): Путь к WAV-файлу.

        Returns:
            str: Транскрибированный текст или пустая строка в случае ошибки.
        """
        try:
            #result = self.audio_model.transcribe(wav_file_path, fp16=torch.cuda.is_available()) # Транскрибация (закомментировано)
            segments, _ = self.audio_model.transcribe(wav_file_path, vad_filter=True,language="en",beam_size=5) # Транскрибация с VAD
            result = list(segments) # Преобразование сегментов в список
        except Exception as e:
            print(f"Ошибка при транскрибации Whisper: {e}")
            return ''
        #return result['text'].strip() # Возврат текста из результата (закомментировано, вероятно, для старой версии whisper)
        full_text = ""
        for segment in result:
        #print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)) # Отладочный вывод сегментов (закомментировано)
            full_text += segment.text + " "  # Добавление текста сегмента с пробелом
        return full_text.strip() # Возврат полного текста без лишних пробелов

    
class APIWhisperTranscriber:
    """Класс для транскрибации аудио с использованием OpenAI Whisper API."""
    def get_transcription(self, wav_file_path: str) -> str:
        """
        Получает транскрипцию для указанного WAV-файла через OpenAI API.

        Args:
            wav_file_path (str): Путь к WAV-файлу.

        Returns:
            str: Транскрибированный текст или пустая строка в случае ошибки.
        """
        try:
            with open(wav_file_path, "rb") as audio_file:
                result = openai.Audio.transcribe("whisper-1", audio_file) # Вызов API для транскрибации
        except Exception as e:
            print(f"Ошибка при транскрибации через API Whisper: {e}")
            return ''
        return result['text'].strip() # Возврат текста из результата