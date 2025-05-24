from typing import Type
from .asr_interface import ASRInterface


class ASRFactory:
    """Фабрика для создания экземпляров систем распознавания речи (ASR)."""
    @staticmethod
    def get_asr_system(system_name: str, **kwargs) -> Type[ASRInterface]:
        """
        Получает экземпляр указанной системы ASR.

        Args:
            system_name (str): Название системы ASR (например, "Faster-Whisper", "FunASR").
            **kwargs: Аргументы, специфичные для конкретной системы ASR.

        Returns:
            Type[ASRInterface]: Экземпляр класса, реализующего интерфейс ASRInterface.

        Raises:
            ValueError: Если указано неизвестное имя системы ASR.
        """
        if system_name == "Faster-Whisper":
            from .faster_whisper_asr import VoiceRecognition as FasterWhisperASR
            return FasterWhisperASR(
                model_path=kwargs.get("model_path"),       # Путь к модели
                download_root=kwargs.get("download_root"), # Корневой каталог для загрузки
                language=kwargs.get("language"),           # Язык
                device=kwargs.get("device"),               # Устройство (cpu, cuda)
            )
        elif system_name == "WhisperCPP":
            # (Предполагается, что WhisperCPPASR принимает kwargs напрямую)
            from .whisper_cpp_asr import VoiceRecognition as WhisperCPPASR
            return WhisperCPPASR(**kwargs)
        elif system_name == "Whisper":
            # (Предполагается, что WhisperASR принимает kwargs напрямую)
            from .openai_whisper_asr import VoiceRecognition as WhisperASR
            return WhisperASR(**kwargs)
        elif system_name == "FunASR":
            from .fun_asr import VoiceRecognition as FunASR
            return FunASR(
                model_name=kwargs.get("model_name"),       # Имя модели
                vad_model=kwargs.get("vad_model"),         # Модель VAD (Voice Activity Detection)
                punc_model=kwargs.get("punc_model"),       # Модель пунктуации
                ncpu=kwargs.get("ncpu"),                   # Количество CPU для использования
                hub=kwargs.get("hub"),                     # Хаб для загрузки моделей (например, 'modelscope')
                device=kwargs.get("device"),               # Устройство
                language=kwargs.get("language"),           # Язык
                use_itn=kwargs.get("use_itn"),             # Использовать ли Inverse Text Normalization
                # sample_rate=kwargs.get("sample_rate"), # Частота дискретизации (закомментировано)
            )
        elif system_name == "AzureASR":
            from .azure_asr import VoiceRecognition as AzureASR
            return AzureASR(
                subscription_key=kwargs.get("subscription_key"), # Ключ подписки Azure
                region=kwargs.get("region"),                     # Регион Azure
                callback=kwargs.get("callback"),                 # Функция обратного вызова
            )
        else:
            raise ValueError(f"Неизвестная система ASR: {system_name}")
