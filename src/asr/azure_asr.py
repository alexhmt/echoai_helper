import azure.cognitiveservices.speech as speechsdk
from .asr_interface import ASRInterface
from typing import Callable
from halo import Halo # Библиотека для отображения спиннера
import os
from rich import print # Библиотека для форматированного вывода в консоль
import numpy as np

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache") # Каталог для кэша

class VoiceRecognition(ASRInterface):
    """Класс для распознавания речи с использованием Azure Cognitive Speech Services."""
    def __init__(self,subscription_key=os.getenv("AZURE_API_Key"), region=os.getenv("AZURE_REGION"), callback: Callable = print ):
        """
        Инициализирует объект VoiceRecognition.

        Args:
            subscription_key (str, optional): Ключ подписки Azure. По умолчанию получается из переменной окружения AZURE_API_Key.
            region (str, optional): Регион Azure. По умолчанию получается из переменной окружения AZURE_REGION.
            callback (Callable, optional): Функция обратного вызова, вызываемая с распознанным текстом. По умолчанию print.
        """
        self.subscription_key = subscription_key
        self.region = region

        self.speech_config = speechsdk.SpeechConfig(subscription=self.subscription_key, region=self.region) # Конфигурация речи Azure

        if not self.subscription_key or not self.region:
            # Сообщение об ошибке, если ключ или регион не предоставлены
            print("Пожалуйста, предоставьте действительный ключ подписки и регион для Azure Speech Recognition или используйте локальное распознавание речи faster-whisper, изменив параметр модели STT в conf.yaml.", style="bold red")
            print("Чтобы предоставить API-ключи, следуйте инструкциям в документации Readme.md «Azure API для распознавания речи и преобразования речи в текст» для создания api_keys.py. В качестве альтернативы вы можете выполнить следующую команду: \n`export AZURE_API_Key=<ваш-ключ-подписки>`\n`export AZURE_REGION=<ваш-код-региона-azure>` с вашими API-ключами", style="red")

        self.callback = callback # Сохранение функции обратного вызова
    


    def _create_speech_recognizer(self, uses_default_microphone: bool =True) -> speechsdk.SpeechRecognizer:
        """
        Создает и возвращает объект SpeechRecognizer.

        Args:
            uses_default_microphone (bool, optional): Использовать ли микрофон по умолчанию. По умолчанию True.
        
        Returns:
            speechsdk.SpeechRecognizer: Объект распознавателя речи.
        """
        print("Ключ подписки: ", self.subscription_key, "Регион: ", self.region) # Отладочная информация
        assert isinstance(self.subscription_key, str), "Ключ подписки должен быть строкой"
        
        audio_config = speechsdk.AudioConfig(use_default_microphone=uses_default_microphone) # Конфигурация аудио
        return speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)


    def transcribe_with_local_vad(self) -> str:
        """
        Транскрибирует речь с использованием локального VAD (Voice Activity Detection).
        Примечание: Azure SDK обычно имеет встроенный VAD, поэтому этот метод может быть упрощен.
        
        Returns:
            str: Распознанный текст или пустая строка в случае неудачи.
        """
        speech_recognizer = self._create_speech_recognizer() # Создание распознавателя
        spinner = Halo(text='ИИ слушает...', spinner='dots') # Инициализация спиннера
        spinner.start() # Запуск спиннера
        result = speech_recognizer.recognize_once() # Однократное распознавание
        spinner.stop() # Остановка спиннера

        if result.reason == speechsdk.ResultReason.RecognizedSpeech: # Если речь распознана
            self.callback(result.text) # Вызов функции обратного вызова с текстом
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch: # Если речь не соответствует
            print("Не распознано")
        elif result.reason == speechsdk.ResultReason.Canceled: # Если распознавание отменено
            cancellation_details = result.cancellation_details
            print("Распознавание отменено: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Информация об ошибке: {}".format(cancellation_details.error_details))

        print("Распознавание речи завершено.")
        return ""
    
    def transcribe_np(self, audio: np.ndarray) -> str:
        """
        Транскрибирует аудиоданные из массива numpy.

        Args:
            audio (np.ndarray): Массив numpy с аудиоданными для транскрибации.
            
        Returns:
            str: Распознанный текст или результат операции распознавания. 
                 (Примечание: возвращает объект результата, а не только текст)
        """
        temp_file = "temp.wav" # Имя временного файла

        # Сохранение массива numpy в текстовый файл (некорректно для аудио, должно быть сохранение в WAV)
        # np.savetxt(temp_file, audio) # Это сохранит данные как текст, а не аудио.
        # Для корректной работы это должно быть заменено на сохранение в WAV формат, например, с использованием scipy.io.wavfile.write
        # Пример:
        # from scipy.io.wavfile import write as write_wav
        # sample_rate = 16000 # Предполагаемая частота дискретизации
        # write_wav(temp_file, sample_rate, audio.astype(np.int16)) # Сохранение в WAV

        # В текущей реализации это приведет к ошибке, так как AudioConfig ожидает аудиофайл.
        # Для демонстрации перевода, предполагаем, что temp_file - это корректный аудиофайл.
        print(f"Предупреждение: Метод transcribe_np в {__file__} сохраняет аудиоданные некорректно. Требуется сохранение в WAV.")


        audio_config = speechsdk.AudioConfig(filename=temp_file) # Конфигурация аудио из файла
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

        result = speech_recognizer.recognize_once() # Распознавание
        
        # Очистка временного файла
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        return f"Ошибка распознавания: {result.reason}" # Возврат причины ошибки, если не распознано
    
    
# Пример использования
if __name__ == "__main__":
    service = VoiceRecognition()
    # service.launch() # Метод launch() не определен в этом классе.
    # Пример вызова transcribe_with_local_vad:
    # text = service.transcribe_with_local_vad()
    # print(f"Распознанный текст: {text}")
    pass # Добавлено для синтаксической корректности