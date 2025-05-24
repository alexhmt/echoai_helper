import abc
import numpy as np

class ASRInterface(metaclass=abc.ABCMeta):
    """Абстрактный базовый класс (интерфейс) для систем распознавания речи (ASR)."""
    
    @abc.abstractmethod
    def transcribe_with_local_vad(self) -> str:
        """
        Активирует микрофон на этом устройстве, транскрибирует аудио при обнаружении паузы в речи с использованием VAD (Voice Activity Detection) 
        и возвращает транскрипцию.
        
        Этот метод должен блокироваться до тех пор, пока не будет доступна транскрипция.
        
        Returns:
            str: Транскрипция речевого аудио.
        """
        pass
    
    @abc.abstractmethod
    def transcribe_np(self, audio: np.ndarray) -> str:
        """
        Транскрибирует речевое аудио в формате массива numpy и возвращает транскрипцию.

        Args:
            audio (np.ndarray): Массив numpy с аудиоданными для транскрибации.
            
        Returns:
            str: Транскрибированный текст.
        """
        pass

    @abc.abstractmethod
    def transcribe_wav(self, audio_path: str) -> str: # Изменено имя аргумента для ясности
        """
        Транскрибирует речевое аудио из WAV-файла и возвращает транскрипцию.

        Args:
            audio_path (str): Путь к WAV-файлу для транскрибации.
            
        Returns:
            str: Транскрибированный текст.
        """
        pass
