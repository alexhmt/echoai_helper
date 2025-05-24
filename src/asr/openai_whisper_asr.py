import numpy as np
import whisper # Импорт библиотеки OpenAI Whisper
from .asr_interface import ASRInterface # Импорт интерфейса ASR
from .asr_with_vad import VoiceRecognitionVAD # Импорт класса для распознавания с VAD


class VoiceRecognition(ASRInterface):
    """Класс для распознавания речи с использованием стандартной библиотеки OpenAI Whisper."""

    def __init__(
        self,
        name: str = "base", # Имя модели Whisper (например, "tiny", "base", "small", "medium", "large")
        download_root: str = None, # Каталог для загрузки модели
        device="cpu", # Устройство для выполнения ("cpu", "cuda")
    ) -> None:
        """
        Инициализирует объект VoiceRecognition для OpenAI Whisper.

        Args:
            name (str, optional): Имя модели Whisper. По умолчанию "base".
            download_root (str, optional): Каталог для загрузки модели. 
                                       По умолчанию None (используется каталог по умолчанию Whisper).
            device (str, optional): Устройство для выполнения модели. По умолчанию "cpu".
        """
        self.model = whisper.load_model(
            name=name,
            device=device,
            download_root=download_root,
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
        # Модель whisper.transcribe() возвращает словарь, из которого нужно извлечь текст.
        # Обычно это result['text']. В старых версиях или в зависимости от конфигурации
        # это может быть список сегментов.
        result = self.model.transcribe(audio)
        
        # Проверка типа результата для корректного извлечения текста
        if isinstance(result, dict) and "text" in result:
            return result["text"].strip()
        elif isinstance(result, list): # Если результат - список сегментов
            full_text = ""
            for segment in result:
                if isinstance(segment, dict) and "text" in segment:
                    full_text += segment["text"] + " "
                elif isinstance(segment, str): # На случай, если сегмент уже строка
                    full_text += segment + " "
            return full_text.strip()
        elif isinstance(result, str): # Если результат уже строка
            return result.strip()
            
        # Если формат результата неизвестен, возвращаем пустую строку или логируем ошибку
        # print(f"Неожиданный формат результата от Whisper: {type(result)}")
        return ""
