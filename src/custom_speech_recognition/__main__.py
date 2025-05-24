import speech_recognition as sr

r = sr.Recognizer()
m = sr.Microphone()

try:
    print("Минутку тишины, пожалуйста...")
    with m as source: r.adjust_for_ambient_noise(source) # Калибровка под окружающий шум
    print("Установлен минимальный порог энергии на {}".format(r.energy_threshold))
    while True:
        print("Скажите что-нибудь!")
        with m as source: audio = r.listen(source) # Прослушивание аудио с микрофона
        print("Понял! Теперь распознаем...")
        try:
            # распознавание речи с использованием Google Speech Recognition
            value = r.recognize_google(audio)

            # мы предполагаем, что пользователь говорит по-английски, поэтому используем формат Unicode U+0000 – U+007F
            # для простоты выводим строку как есть
            print("Вы сказали: {}".format(value))
        except sr.UnknownValueError:
            print("Ой! Не удалось распознать речь")
        except sr.RequestError as e:
            print("Ох! Не удалось запросить результаты у службы Google Speech Recognition; {0}".format(e))
except KeyboardInterrupt:
    pass # Выход по Ctrl+C
