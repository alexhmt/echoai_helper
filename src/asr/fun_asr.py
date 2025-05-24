import numpy as np
from funasr import AutoModel # Импорт AutoModel из библиотеки funasr
from .asr_interface import ASRInterface # Импорт интерфейса ASR
from .asr_with_vad import VoiceRecognitionVAD # Импорт класса для распознавания с VAD

import re # Модуль для работы с регулярными выражениями
import soundfile as sf # Библиотека для работы с аудиофайлами
import io # Модуль для работы с потоками ввода-вывода
import torch # Библиотека PyTorch

# paraformer-zh - это многофункциональная модель ASR
# используйте VAD, пунктуацию, определение диктора (spk) или нет по вашему усмотрению


class VoiceRecognition(ASRInterface):
    """Класс для распознавания речи с использованием моделей FunASR."""

    def __init__(
        self,
        model_name: str = "iic/SenseVoiceSmall", # Имя или путь к основной модели ASR
        language: str = "auto", # Язык для распознавания ('auto' для автоматического определения)
        #vad_model: str = "fsmn-vad", # Модель детекции голосовой активности (VAD) (закомментировано)
        vad_model = None, # Модель VAD, по умолчанию None
        punc_model=None, # Модель пунктуации, по умолчанию None
        ncpu: int = None, # Количество ядер CPU для использования
        hub: str = None, # Хаб для загрузки моделей (например, 'modelscope', 'hf')
        device: str = "cpu", # Устройство для выполнения модели ("cpu", "cuda")
        sample_rate: int = 16000, # Частота дискретизации аудио
        use_itn: bool = False, # Использовать ли инверсную нормализацию текста (ITN)
    ) -> None:
        """
        Инициализирует объект VoiceRecognition для FunASR.

        Args:
            model_name (str, optional): Имя или путь к модели FunASR. По умолчанию "iic/SenseVoiceSmall".
            language (str, optional): Язык для распознавания. По умолчанию "auto".
            vad_model (str, optional): Имя или путь к модели VAD. По умолчанию None.
            punc_model (str, optional): Имя или путь к модели пунктуации. По умолчанию None.
            ncpu (int, optional): Количество ядер CPU. По умолчанию определяется библиотекой.
            hub (str, optional): Хаб для загрузки моделей. По умолчанию None.
            device (str, optional): Устройство для вычислений. По умолчанию "cpu".
            sample_rate (int, optional): Ожидаемая частота дискретизации. По умолчанию 16000.
            use_itn (bool, optional): Использовать ли инверсную нормализацию текста. По умолчанию False.
        """
        
        self.model = AutoModel(
            model=model_name,
            vad_model=vad_model,
            ncpu=ncpu,
            hub=hub,
            device=device,
            punc_model=punc_model,
            disable_update=True, # Отключить автоматическое обновление моделей
            #spk_model="cam++", # Модель определения диктора (закомментировано)
        )
        self.sample_rate = sample_rate
        self.use_itn = use_itn
        self.language = language

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
    
    def transcribe_wav(self, audio_path: str) -> str: # Изменено имя аргумента для ясности
        """
        Транскрибирует аудио из WAV-файла.

        Args:
            audio_path (str): Путь к WAV-файлу.

        Returns:
            str: Распознанный текст или пустая строка в случае ошибки.
        """
        
        #audio_tensor = torch.tensor(audio, dtype=torch.float32) # Преобразование в тензор (закомментировано, т.к. input может быть путем)
        
        # Генерация текста с помощью модели FunASR
        res = self.model.generate(
            input=audio_path, # Входные данные (путь к файлу или аудиоданные)
            batch_size_s=300, # Размер батча в секундах
            use_itn=self.use_itn, # Использование ITN
            language=self.language, # Язык
        )
        
        full_text = res[0]["text"] # Извлечение текста из результата

        # Модель SenseVoiceSmall может выводить некоторые теги,
        # например: '<|zh|><|NEUTRAL|><|Speech|><|woitn|>欢迎大家来体验达摩院推出的语音识别模型'
        # мы должны удалить эти теги из результата

        # удаление тегов
        full_text = re.sub(r'<\|.*?\|>', '', full_text)
        # теги также могут выглядеть так: '< | en | > < | EMO _ UNKNOWN | > < | S pe ech | > < | wo itn | > ', поэтому...
        full_text = re.sub(r'< \|.*?\| >', '', full_text)
        
        return full_text.strip() # Возврат очищенного текста

    def transcribe_np(self, audio: np.ndarray) -> str:
        """
        Транскрибирует аудиоданные из массива numpy.

        Args:
            audio (np.ndarray): Массив numpy с аудиоданными для транскрибации.

        Returns:
            str: Распознанный текст или пустая строка в случае ошибки.
        """
        
        audio_tensor = torch.tensor(audio, dtype=torch.float32) # Преобразование аудио в тензор PyTorch
        
        # Генерация текста
        res = self.model.generate(
            input=audio_tensor,
            batch_size_s=300,
            use_itn=self.use_itn,
            language=self.language,
        )
        
        full_text = res[0]["text"]

        # Модель SenseVoiceSmall может выводить некоторые теги
        # например: '<|zh|><|NEUTRAL|><|Speech|><|woitn|>欢迎大家来体验达摩院推出的语音识别模型'
        # мы должны удалить эти теги из результата

        # удаление тегов
        full_text = re.sub(r'<\|.*?\|>', '', full_text)
        # теги также могут выглядеть так: '< | en | > < | EMO _ UNKNOWN | > < | S pe ech | > < | wo itn | > ', поэтому...
        full_text = re.sub(r'< \|.*?\| >', '', full_text)
        
        return full_text.strip()

    def _numpy_to_wav_in_memory(self, numpy_array: np.ndarray, sample_rate: int) -> io.BytesIO:
        """
        Преобразует массив numpy в WAV-формат в памяти.

        Args:
            numpy_array (np.ndarray): Аудиоданные в виде массива numpy.
            sample_rate (int): Частота дискретизации.

        Returns:
            io.BytesIO: Объект BytesIO, содержащий аудиоданные в формате WAV.
        """
        memory_file = io.BytesIO() # Создание объекта BytesIO в памяти
        # Запись массива numpy в объект BytesIO в формате WAV
        sf.write(memory_file, numpy_array, sample_rate, format='WAV')
        memory_file.seek(0) # Перемещение указателя в начало файла
        
        return memory_file
