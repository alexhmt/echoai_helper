import numpy as np
from faster_whisper import WhisperModel # Импорт модели Whisper из faster_whisper
from .asr_interface import ASRInterface # Импорт интерфейса ASR
from .asr_with_vad import VoiceRecognitionVAD # Импорт класса для распознавания с VAD


class VoiceRecognition(ASRInterface):
    """Класс для распознавания речи с использованием модели Faster Whisper."""

    BEAM_SEARCH = True # Использовать ли поиск лучом (beam search)
    SAMPLE_RATE = 16000  # Частота дискретизации для входного потока

    def __init__(
        self,
        model_path: str = "distil-medium.en", # Путь или имя модели
        download_root: str = None, # Корневой каталог для загрузки модели
        language: str = "en", # Язык распознавания
        device: str = "auto", # Устройство для вычислений ("auto", "cpu", "cuda")
    ) -> None:
        """
        Инициализирует объект VoiceRecognition.

        Args:
            model_path (str, optional): Путь к локальной модели или имя модели для загрузки. 
                                       По умолчанию "distil-medium.en".
            download_root (str, optional): Каталог для загрузки модели. По умолчанию None (используется каталог кэша faster-whisper).
            language (str, optional): Язык распознавания (например, "en", "ru"). По умолчанию "en".
            device (str, optional): Устройство для выполнения модели ("auto", "cpu", "cuda"). 
                                   По умолчанию "auto".
        """
        self.MODEL_PATH = model_path
        self.LANG = language

        # Инициализация модели WhisperModel
        self.model = WhisperModel(model_path, download_root=download_root, device=device, compute_type="float32")
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
            str: Распознанный текст или пустая строка, если ничего не распознано.
        """

        # Транскрибация аудио с помощью модели
        segments, info = self.model.transcribe(
            audio,
            beam_size=5 if self.BEAM_SEARCH else 1, # Размер луча для поиска
            language=self.LANG, # Язык
            condition_on_previous_text=False, # Не учитывать предыдущий текст
        )

        text = [segment.text for segment in segments] # Сбор текста из всех сегментов

        if not text:
            return "" # Возврат пустой строки, если текст не распознан
        else:
            return "".join(text) # Объединение текстовых сегментов
