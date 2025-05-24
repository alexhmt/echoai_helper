import aifc
import audioop
import io
import os
import platform
import stat
import subprocess
import sys
import wave


class AudioData(object):
    """
    Создает новый экземпляр ``AudioData``, представляющий монофонические аудиоданные.

    Необработанные аудиоданные задаются параметром ``frame_data``, который представляет собой последовательность байтов, представляющих аудиосэмплы. Это структура данных кадра, используемая форматом PCM WAV.

    Ширина каждого сэмпла в байтах задается параметром ``sample_width``. Каждая группа из ``sample_width`` байтов представляет один аудиосэмпл.

    Предполагается, что аудиоданные имеют частоту дискретизации ``sample_rate`` сэмплов в секунду (Герц).

    Обычно экземпляры этого класса получаются из ``recognizer_instance.record`` или ``recognizer_instance.listen``, или в обратном вызове для ``recognizer_instance.listen_in_background``, а не создаются напрямую.
    """

    def __init__(self, frame_data, sample_rate, sample_width):
        assert sample_rate > 0, "Частота дискретизации должна быть положительным целым числом"
        assert (
            sample_width % 1 == 0 and 1 <= sample_width <= 4
        ), "Ширина сэмпла должна быть целым числом от 1 до 4 включительно"
        self.frame_data = frame_data # Необработанные аудиоданные (байты)
        self.sample_rate = sample_rate # Частота дискретизации (Гц)
        self.sample_width = int(sample_width) # Ширина сэмпла (байты)

    def get_segment(self, start_ms=None, end_ms=None):
        """
        Возвращает новый экземпляр ``AudioData``, обрезанный до заданного временного интервала. Другими словами, экземпляр ``AudioData`` с теми же аудиоданными, но начинающийся с ``start_ms`` миллисекунд и заканчивающийся на ``end_ms`` миллисекунд.

        Если не указано, ``start_ms`` по умолчанию соответствует началу аудио, а ``end_ms`` — концу.
        """
        assert (
            start_ms is None or start_ms >= 0
        ), "``start_ms`` должен быть неотрицательным числом"
        assert end_ms is None or end_ms >= (
            0 if start_ms is None else start_ms
        ), "``end_ms`` должен быть неотрицательным числом, большим или равным ``start_ms``"
        if start_ms is None: # Если начальное время не указано
            start_byte = 0 # Начальный байт - 0
        else:
            # Расчет начального байта на основе времени в мс, частоты дискретизации и ширины сэмпла
            start_byte = int(
                (start_ms * self.sample_rate * self.sample_width) // 1000
            )
        if end_ms is None: # Если конечное время не указано
            end_byte = len(self.frame_data) # Конечный байт - конец данных
        else:
            # Расчет конечного байта
            end_byte = int(
                (end_ms * self.sample_rate * self.sample_width) // 1000
            )
        # Возврат нового объекта AudioData с обрезанными данными
        return AudioData(
            self.frame_data[start_byte:end_byte],
            self.sample_rate,
            self.sample_width,
        )

    def get_raw_data(self, convert_rate=None, convert_width=None):
        """
        Возвращает байтовую строку, представляющую необработанные данные кадра для аудио, представленного экземпляром ``AudioData``.

        Если указан ``convert_rate`` и частота дискретизации аудио не равна ``convert_rate`` Гц, результирующее аудио передискретизируется для соответствия.

        Если указан ``convert_width`` и аудиосэмплы не имеют ширину ``convert_width`` байт каждый, результирующее аудио преобразуется для соответствия.

        Запись этих байтов непосредственно в файл приводит к созданию действительного `файла необработанного аудио/PCM <https://en.wikipedia.org/wiki/Raw_audio_format>`__.
        """
        assert (
            convert_rate is None or convert_rate > 0
        ), "Частота дискретизации для преобразования должна быть положительным целым числом"
        assert convert_width is None or (
            convert_width % 1 == 0 and 1 <= convert_width <= 4
        ), "Ширина сэмпла для преобразования должна быть целым числом от 1 до 4 включительно"

        raw_data = self.frame_data # Исходные необработанные данные

        # убедимся, что беззнаковое 8-битное аудио (которое использует беззнаковые сэмплы) обрабатывается так же, как аудио с большей шириной сэмпла (которое использует знаковые сэмплы)
        if self.sample_width == 1:
            raw_data = audioop.bias(
                raw_data, 1, -128
            )  # вычитаем 128 из каждого сэмпла, чтобы они вели себя как знаковые сэмплы

        # передискретизация аудио с желаемой частотой, если указано
        if convert_rate is not None and self.sample_rate != convert_rate:
            raw_data, _ = audioop.ratecv( # Преобразование частоты дискретизации
                raw_data,
                self.sample_width,
                1, # Количество каналов (моно)
                self.sample_rate,
                convert_rate,
                None, # Состояние (state) для последовательных вызовов
            )

        # преобразование сэмплов к желаемой ширине, если указано
        if convert_width is not None and self.sample_width != convert_width:
            if (
                convert_width == 3
            ):  # мы преобразуем аудио в 24-битное (обход проблемы https://bugs.python.org/issue12866)
                raw_data = audioop.lin2lin(
                    raw_data, self.sample_width, 4
                )  # сначала преобразуем аудио в 32-битное, которое всегда поддерживается
                try:
                    audioop.bias(
                        b"", 3, 0
                    )  # проверяем, поддерживается ли 24-битное аудио (например, ``audioop`` в Python 3.3 и ниже не поддерживает ширину сэмпла 3, в то время как Python 3.4+ поддерживает)
                except (
                    audioop.error # Перехватываем ошибку audioop
                ):  # эта версия audioop не поддерживает 24-битное аудио (вероятно, Python 3.3 или младше)
                    raw_data = b"".join(
                        raw_data[i + 1: i + 4] # Берем 3 байта из 4 (отбрасываем старший байт)
                        for i in range(0, len(raw_data), 4)
                    )  # так как мы в little-endian, мы отбрасываем первый байт из каждого 32-битного сэмпла, чтобы получить 24-битный сэмпл
                else:  # 24-битное аудио полностью поддерживается, нам не нужно ничего подменять
                    raw_data = audioop.lin2lin( # Преобразуем линейно
                        raw_data, 4, convert_width # Из 32-битного (после предыдущего шага) в целевую ширину
                    ) # В оригинале было self.sample_width, но после преобразования в 4 байта, нужно использовать 4
            else: # Для других ширин (1, 2, 4)
                raw_data = audioop.lin2lin(
                    raw_data, self.sample_width, convert_width
                )

        # если на выходе 8-битное аудио с беззнаковыми сэмплами, преобразуем сэмплы, которые мы обрабатывали как знаковые, обратно в беззнаковые
        if convert_width == 1:
            raw_data = audioop.bias(
                raw_data, 1, 128
            )  # добавляем 128 к каждому сэмплу, чтобы они снова вели себя как беззнаковые сэмплы

        return raw_data

    def get_wav_data(self, convert_rate=None, convert_width=None):
        """
        Возвращает байтовую строку, представляющую содержимое WAV-файла, содержащего аудио, представленное экземпляром ``AudioData``.

        Если указан ``convert_width`` и аудиосэмплы не имеют ширину ``convert_width`` байт каждый, результирующее аудио преобразуется для соответствия.

        Если указан ``convert_rate`` и частота дискретизации аудио не равна ``convert_rate`` Гц, результирующее аудио передискретизируется для соответствия.

        Запись этих байтов непосредственно в файл приводит к созданию действительного `WAV-файла <https://en.wikipedia.org/wiki/WAV>`__.
        """
        raw_data = self.get_raw_data(convert_rate, convert_width) # Получение необработанных данных с возможным преобразованием
        sample_rate = (
            self.sample_rate if convert_rate is None else convert_rate
        )
        sample_width = (
            self.sample_width if convert_width is None else convert_width
        )

        # генерация содержимого WAV-файла
        with io.BytesIO() as wav_file: # Использование BytesIO для записи в память
            wav_writer = wave.open(wav_file, "wb") # Открытие WAV для записи в двоичном режиме
            try:  # обратите внимание, что мы не можем использовать контекстный менеджер, так как он был добавлен только в Python 3.4
                wav_writer.setframerate(sample_rate) # Установка частоты дискретизации
                wav_writer.setsampwidth(sample_width) # Установка ширины сэмпла
                wav_writer.setnchannels(1) # Установка количества каналов (моно)
                wav_writer.writeframes(raw_data) # Запись аудиокадров
                wav_data = wav_file.getvalue() # Получение содержимого WAV-файла из буфера
            finally:  # убедимся, что ресурсы освобождены
                wav_writer.close()
        return wav_data

    def get_aiff_data(self, convert_rate=None, convert_width=None):
        """
        Возвращает байтовую строку, представляющую содержимое файла AIFF-C, содержащего аудио, представленное экземпляром ``AudioData``.

        Если указан ``convert_width`` и аудиосэмплы не имеют ширину ``convert_width`` байт каждый, результирующее аудио преобразуется для соответствия.

        Если указан ``convert_rate`` и частота дискретизации аудио не равна ``convert_rate`` Гц, результирующее аудио передискретизируется для соответствия.

        Запись этих байтов непосредственно в файл приводит к созданию действительного `файла AIFF-C <https://en.wikipedia.org/wiki/Audio_Interchange_File_Format>`__.
        """
        raw_data = self.get_raw_data(convert_rate, convert_width)
        sample_rate = (
            self.sample_rate if convert_rate is None else convert_rate
        )
        sample_width = (
            self.sample_width if convert_width is None else convert_width
        )

        # формат AIFF является big-endian, поэтому нам нужно преобразовать необработанные данные little-endian в big-endian
        if hasattr(
            audioop, "byteswap"
        ):  # ``audioop.byteswap`` был добавлен только в Python 3.4
            raw_data = audioop.byteswap(raw_data, sample_width)
        else:  # вручную инвертируем байты каждого сэмпла, что медленнее, но достаточно хорошо работает в качестве запасного варианта
            raw_data = raw_data[sample_width - 1:: -1] + b"".join(
                raw_data[i + sample_width: i: -1]
                for i in range(sample_width - 1, len(raw_data), sample_width)
            )

        # генерация содержимого файла AIFF-C
        with io.BytesIO() as aiff_file:
            aiff_writer = aifc.open(aiff_file, "wb") # Открытие AIFF для записи
            try:  # обратите внимание, что мы не можем использовать контекстный менеджер, так как он был добавлен только в Python 3.4
                aiff_writer.setframerate(sample_rate)
                aiff_writer.setsampwidth(sample_width)
                aiff_writer.setnchannels(1)
                aiff_writer.writeframes(raw_data)
                aiff_data = aiff_file.getvalue()
            finally:  # убедимся, что ресурсы освобождены
                aiff_writer.close()
        return aiff_data

    def get_flac_data(self, convert_rate=None, convert_width=None):
        """
        Возвращает байтовую строку, представляющую содержимое файла FLAC, содержащего аудио, представленное экземпляром ``AudioData``.

        Обратите внимание, что 32-битный FLAC не поддерживается. Если аудиоданные 32-битные и ``convert_width`` не указан, результирующий FLAC будет 24-битным.

        Если указан ``convert_rate`` и частота дискретизации аудио не равна ``convert_rate`` Гц, результирующее аудио передискретизируется для соответствия.

        Если указан ``convert_width`` и аудиосэмплы не имеют ширину ``convert_width`` байт каждый, результирующее аудио преобразуется для соответствия.

        Запись этих байтов непосредственно в файл приводит к созданию действительного `файла FLAC <https://en.wikipedia.org/wiki/FLAC>`__.
        """
        assert convert_width is None or (
            convert_width % 1 == 0 and 1 <= convert_width <= 3
        ), "Ширина сэмпла для преобразования должна быть целым числом от 1 до 3 включительно"

        if (
            self.sample_width > 3 and convert_width is None
        ):  # результирующие данные WAV будут 32-битными, что не может быть преобразовано в FLAC с помощью нашего кодировщика
            convert_width = 3  # наибольшая поддерживаемая ширина сэмпла — 24 бита, поэтому мы ограничим ширину сэмпла этим значением

        # запуск конвертера FLAC с данными WAV для получения данных FLAC
        wav_data = self.get_wav_data(convert_rate, convert_width)
        flac_converter = get_flac_converter() # Получение пути к конвертеру FLAC
        if (
            os.name == "nt"
        ):  # в Windows указываем, что процесс должен запускаться без отображения консольного окна
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= (
                subprocess.STARTF_USESHOWWINDOW
            )  # указываем, что поле wShowWindow структуры `startup_info` содержит значение
            startup_info.wShowWindow = (
                subprocess.SW_HIDE
            )  # указываем, что консольное окно должно быть скрыто
        else:
            startup_info = None  # информация о запуске по умолчанию
        process = subprocess.Popen( # Запуск процесса конвертации
            [
                flac_converter,
                "--stdout", # Вывод в stdout
                "--totally-silent",  # полностью тихий режим, чтобы вывод программы не смешивался с данными
                "--best",  # наивысший доступный уровень сжатия
                "-",  # содержимое входного файла будет передано через stdin
            ],
            stdin=subprocess.PIPE, # Входной поток
            stdout=subprocess.PIPE, # Выходной поток
            startupinfo=startup_info, # Информация о запуске
        )
        flac_data, stderr = process.communicate(wav_data) # Передача данных WAV и получение данных FLAC
        return flac_data


def get_flac_converter():
    """Возвращает абсолютный путь к исполняемому файлу конвертера FLAC или вызывает OSError, если ни один не найден."""
    flac_converter = shutil_which("flac")  # сначала проверяем установленную версию
    if flac_converter is None:  # утилита flac не установлена
        base_path = os.path.dirname(
            os.path.abspath(__file__)
        )  # каталог текущего файла модуля, где хранятся все встроенные двоичные файлы FLAC
        system, machine = platform.system(), platform.machine() # Получение информации о системе
        if system == "Windows" and machine in { # Для Windows
            "i686",
            "i786",
            "x86",
            "x86_64",
            "AMD64",
        }:
            flac_converter = os.path.join(base_path, "flac-win32.exe")
        elif system == "Darwin" and machine in { # Для macOS
            "i686",
            "i786",
            "x86",
            "x86_64",
            "AMD64",
            "arm64", # Добавлена поддержка arm64 для Apple Silicon
        }:
            flac_converter = os.path.join(base_path, "flac-mac")
        elif system == "Linux" and machine in {"i686", "i786", "x86"}: # Для Linux 32-bit
            flac_converter = os.path.join(base_path, "flac-linux-x86")
        elif system == "Linux" and machine in {"x86_64", "AMD64"}: # Для Linux 64-bit
            flac_converter = os.path.join(base_path, "flac-linux-x86_64")
        else:  # конвертер FLAC недоступен
            raise OSError(
                "Утилита для преобразования FLAC недоступна - рассмотрите возможность установки приложения командной строки FLAC, выполнив `apt-get install flac` или эквивалентную команду для вашей операционной системы"
            )

    # помечаем конвертер FLAC как исполняемый, если это возможно
    try:
        # обработка известной проблемы при запуске в docker:
        # запуск исполняемого файла сразу после chmod() может привести к OSError "Text file busy"
        # исправление: сброс ФС с помощью sync
        if not os.access(flac_converter, os.X_OK): # Если нет прав на выполнение
            stat_info = os.stat(flac_converter) # Получение текущих прав
            os.chmod(flac_converter, stat_info.st_mode | stat.S_IEXEC) # Добавление прав на выполнение
            if "Linux" in platform.system(): # Для Linux выполнить sync
                # os.sync() доступен в Python 3.3+
                if sys.version_info >= (3, 3):
                    os.sync() 
                else: # pragma: no cover
                    os.system("sync") # Для старых версий Python

    except OSError: # pragma: no cover
        pass # Игнорировать ошибки chmod, если они возникают

    return flac_converter


def shutil_which(pgm):
    """Совместимость с Python 2: бэкпорт ``shutil.which()`` из Python 3."""
    path = os.getenv("PATH") # Получение переменной окружения PATH
    if path is None: return None # Если PATH не установлен
    for p in path.split(os.path.pathsep): # Перебор всех путей в PATH
        p_joined = os.path.join(p, pgm) # Формирование полного пути к программе
        if os.path.exists(p_joined) and os.access(p_joined, os.X_OK): # Проверка существования и прав на выполнение
            return p_joined
    return None # Если программа не найдена
