# Оригинальный код Дэвида Нг в [GlaDOS](https://github.com/dnhkng/GlaDOS), лицензированный по лицензии MIT
# https://opensource.org/licenses/MIT# 
# Модификации Yi-Ting Chiu в рамках OpenLLM-VTuber, лицензировано по лицензии MIT
# https://opensource.org/licenses/MIT
# 
#

import numpy as np
import onnxruntime as ort # Библиотека для выполнения моделей ONNX

SAMPLE_RATE = 16000 # Частота дискретизации по умолчанию


class VAD:
    """Класс для детекции голосовой активности (VAD) с использованием модели ONNX."""
    
    # Начальные состояния скрытых слоев (h) и ячеек памяти (c) для LSTM-подобных моделей
    _initial_h = np.zeros((2, 1, 64)).astype("float32")
    _initial_c = np.zeros((2, 1, 64)).astype("float32")

    def __init__(self, model_path: str, window_size_samples: int = int(SAMPLE_RATE / 10)):
        """
        Инициализирует объект VAD.

        Args:
            model_path (str): Путь к файлу модели VAD в формате ONNX.
            window_size_samples (int, optional): Размер окна в семплах для обработки. 
                                                 По умолчанию равен SAMPLE_RATE / 10 (100 мс при 16 кГц).
        """
        # Создание сессии ONNX Runtime для выполнения на CPU
        self.ort_sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.window_size_samples = window_size_samples # Размер окна для обработки аудио
        self.sr = SAMPLE_RATE # Частота дискретизации
        self._h = self._initial_h # Текущее состояние h
        self._c = self._initial_c # Текущее состояние c

    def reset(self):
        """Сбрасывает внутренние состояния (h и c) модели к начальным значениям."""
        self._h = self._initial_h
        self._c = self._initial_c

    def process_chunk(self, chunk: np.ndarray) -> np.ndarray:
        """
        Обрабатывает один чанк (фрагмент) аудиоданных.

        Args:
            chunk (np.ndarray): Аудиочанк в виде массива numpy.

        Returns:
            np.ndarray: Результат детекции VAD для этого чанка (обычно вероятность наличия голоса).
        """
        # Подготовка входных данных для модели ONNX
        ort_inputs = {
            "input": np.expand_dims(chunk, 0), # Добавление измерения батча
            "h": self._h, # Предыдущее состояние h
            "c": self._c, # Предыдущее состояние c
            "sr": np.array(self.sr, dtype="int64"), # Частота дискретизации
        }
        # Выполнение модели и получение выходных данных и новых состояний h и c
        out, self._h, self._c = self.ort_sess.run(None, ort_inputs)
        return np.squeeze(out) # Удаление лишних измерений из результата

    def process_file(self, audio: np.ndarray) -> np.ndarray:
        """
        Обрабатывает весь аудиофайл (представленный как массив numpy) по чанкам.

        Args:
            audio (np.ndarray): Аудиоданные всего файла.

        Returns:
            np.ndarray: Массив результатов детекции VAD для каждого чанка.
        """
        self.reset() # Сброс состояний перед обработкой нового файла
        results = [] # Список для хранения результатов по чанкам
        # Итерация по аудиоданным с шагом window_size_samples
        for i in range(0, len(audio), self.window_size_samples):
            chunk = audio[i : i + self.window_size_samples] # Получение текущего чанка
            if len(chunk) < self.window_size_samples: # Если чанк короче необходимого, прервать
                break
            # Подготовка и выполнение модели аналогично process_chunk
            ort_inputs = {
                "input": np.expand_dims(chunk, 0),
                "h": self._h,
                "c": self._c,
                "sr": np.array(self.sr, dtype="int64"),
            }
            out, self._h, self._c = self.ort_sess.run(None, ort_inputs)
            results.append(np.squeeze(out)) # Добавление результата в список
        results = np.stack(results, axis=0) # Объединение результатов по чанкам в один массив
        return results