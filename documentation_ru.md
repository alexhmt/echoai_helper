# Файл: main.py

## Функции

### `validate_phrase_timeout(value)`
 - **Параметры:**
   - `value`
 - **Тип возвращаемого значения:** `bool`

### `validate_buffer_chunks(value)`
 - **Параметры:**
   - `value`
 - **Тип возвращаемого значения:** `bool`

### `create_dropdown(root, options, row, column)`
 - **Параметры:**
   - `root`
   - `options`
   - `row`
   - `column`
 - **Тип возвращаемого значения:** `tuple` (`ctk.CTkOptionMenu`, `ctk.StringVar`)

### `create_buffer_config(root, transcriber)`
 - **Параметры:**
   - `root`
   - `transcriber`
 - **Тип возвращаемого значения:** `ctk.CTkFrame`

### `create_timeout_config(root)`
 - **Параметры:**
   - `root`
 - **Тип возвращаемого значения:** `ctk.CTkFrame`

### `write_in_textbox(textbox, text)`
 - **Параметры:**
   - `textbox`
   - `text`

### `update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state, transcript_ui)`
 - **Параметры:**
   - `responder`
   - `textbox`
   - `update_interval_slider_label`
   - `update_interval_slider`
   - `freeze_state`
   - `transcript_ui`

### `clear_context_(transcriber, audio_queue)`
 - **Параметры:**
   - `transcriber`
   - `audio_queue`

### `clear_context(transcriber, audio_queue, transcript_ui)`
 - **Докстринг:** Очищает весь контекст
 - **Параметры:**
   - `transcriber`
   - `audio_queue`
   - `transcript_ui`

### `create_ui_components(root, response_manager, transcriber, audio_queue)`
 - **Докстринг:** Создает и настраивает все компоненты пользовательского интерфейса
 - **Параметры:**
   - `root`
   - `response_manager`
   - `transcriber`
   - `audio_queue`
 - **Тип возвращаемого значения:** `tuple`

### `main()`

# Файл: src/AudioRecorder.py

## Классы

## `BaseRecorder`
 - **Докстринг:** Базовый класс для записи аудио.
 - **Методы:**
   ### `__init__(self, source, source_name)`
     - **Параметры:**
       - `self`
       - `source`
       - `source_name`
   ### `adjust_for_noise(self, device_name, msg)`
     - **Докстринг:** Регулирует распознаватель с учетом окружающего шума.
     - **Параметры:**
       - `self`
       - `device_name`
       - `msg`
   ### `record_into_queue(self, audio_queue)`
     - **Докстринг:** Записывает аудио в очередь.
     - **Параметры:**
       - `self`
       - `audio_queue`

## `DefaultMicRecorder(BaseRecorder)`
 - **Докстринг:** Класс для записи с микрофона по умолчанию.
 - **Методы:**
   ### `__init__(self)`
     - **Параметры:**
       - `self`

## `DefaultSpeakerRecorder(BaseRecorder)`
 - **Докстринг:** Класс для записи с динамиков по умолчанию.
 - **Методы:**
   ### `__init__(self)`
     - **Параметры:**
       - `self`

# Файл: src/AudioTranscriber.py

## Классы

## `AudioTranscriber`
 - **Докстринг:** Класс для транскрибации аудио с микрофона и системных звуков (динамика). Управляет сбором аудиоданных, их обработкой и обновлением структуры транскрипции.
 - **Методы:**
   ### `__init__(self, mic_source, speaker_source, model, response_manager)`
     - **Параметры:**
       - `self`
       - `mic_source`
       - `speaker_source`
       - `model`
       - `response_manager`
   ### `transcribe_audio_queue(self, audio_queue)`
     - **Докстринг:** Обрабатывает очередь аудиоданных, транскрибирует их и обновляет транскрипцию.
     - **Параметры:**
       - `self`
       - `audio_queue`
   ### `update_last_sample_and_phrase_status(self, who_spoke, data, time_spoken)`
     - **Докстринг:** Обновляет последний семпл, буфер чанков и статус фразы для указанного источника.
     - **Параметры:**
       - `self`
       - `who_spoke`
       - `data`
       - `time_spoken`
   ### `process_mic_data(self, data, temp_file_name)`
     - **Докстринг:** Обрабатывает данные с микрофона и сохраняет их в WAV файл.
     - **Параметры:**
       - `self`
       - `data`
       - `temp_file_name`
   ### `process_speaker_data(self, data, temp_file_name)`
     - **Докстринг:** Обрабатывает данные с динамика и сохраняет их в WAV файл.
     - **Параметры:**
       - `self`
       - `data`
       - `temp_file_name`
   ### `update_transcript(self, who_spoke, text, time_spoken)`
     - **Докстринг:** Обновляет различные структуры данных транскрипции на основе нового текста.
     - **Параметры:**
       - `self`
       - `who_spoke`
       - `text`
       - `time_spoken`
   ### `_reset_source_info(self, source_info, time_spoken)`
     - **Докстринг:** Сбрасывает состояние информации об источнике для начала новой фразы.
     - **Параметры:**
       - `self`
       - `source_info`
       - `time_spoken`
   ### `_update_all_transcripts(self, speaker_type, record, method='insert')`
     - **Докстринг:** Обновляет все структуры данных транскрипции (обычную, структурированную, комбинированную).
     - **Параметры:**
       - `self`
       - `speaker_type`
       - `record`
       - `method` (по умолчанию: `'insert'`)
   ### `get_transcript(self)`
     - **Докстринг:** Возвращает отформатированные данные транскрипции для отображения.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `dict`
   ### `get_lastContent(self)`
     - **Докстринг:** Получает содержимое последней записи от "Speaker".
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `clear_transcript_data(self)`
     - **Докстринг:** Очищает все данные транскрипции и сбрасывает состояние источников аудио.
     - **Параметры:**
       - `self`

# Файл: src/GPTResponder.py

## Классы

## `GPTResponder`
 - **Методы:**
   ### `__init__(self, response_manager)`
     - **Параметры:**
       - `self`
       - `response_manager`
   ### `_initialize_openai(self) -> bool`
     - **Докстринг:** Инициализирует конфигурацию OpenAI или совместимого LLM.
       **Возвращает:**
       `bool`: True в случае успешной инициализации, иначе False.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `bool`
   ### `_generate_response_from_transcript(self, lastContent, latest_response_text="", latest_response_q_text="", current_response_id=None)`
     - **Докстринг:** Генерирует потоковый ответ из содержимого транскрипции.
       **Аргументы:**
       `lastContent` (str): Последнее содержимое транскрипции.
       `latest_response_text` (str): Содержимое предыдущего ответа.
       `latest_response_q_text` (str): Содержимое предыдущего вопроса.
       `current_response_id` (str): ID текущего ответа.
       **Возвращает (Yields):**
       `str`: Сгенерированная часть содержимого ответа.
     - **Параметры:**
       - `self`
       - `lastContent`
       - `latest_response_text` (по умолчанию: `""`)
       - `latest_response_q_text` (по умолчанию: `""`)
       - `current_response_id` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `str` (итератор)
   ### `respond_to_transcriber(self, transcriber)`
     - **Докстринг:** Постоянно прослушивает и отвечает на вывод транскрибатора.
       **Аргументы:**
       `transcriber`: Экземпляр транскрибатора.
     - **Параметры:**
       - `self`
       - `transcriber`
   ### `update_response_interval(self, interval)`
     - **Параметры:**
       - `self`
       - `interval`

# Файл: src/ResponseManager.py

## Классы

## `Response`
 - **Докстринг:** Класс данных для хранения информации об одном ответе.
 - **Методы:**
   ### `to_dict(self)`
     - **Докстринг:** Преобразует объект Response в словарь, пригодный для сериализации.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `dict`

## `ResponseManager`
 - **Докстринг:** Класс для управления ответами. Отвечает за создание, обновление, хранение и экспорт ответов.
 - **Методы:**
   ### `__init__(self)`
     - **Параметры:**
       - `self`
   ### `_convert_to_local_time(self, dt: datetime) -> datetime`
     - **Докстринг:** Преобразует время в локальную временную зону.
     - **Параметры:**
       - `self`
       - `dt: datetime`
     - **Тип возвращаемого значения:** `datetime`
   ### `_format_datetime(self, dt: Optional[datetime]) -> Optional[str]`
     - **Докстринг:** Форматирует дату и время в строку локального времени.
     - **Параметры:**
       - `self`
       - `dt: Optional[datetime]`
     - **Тип возвращаемого значения:** `Optional[str]`
   ### `export_responses(self) -> list`
     - **Докстринг:** Экспортирует все данные ответов в формате, пригодном для сериализации.
       **Возвращает:**
       `list`: Список, содержащий все данные ответов.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `list`
   ### `save_responses_to_file(self, filepath: str) -> bool`
     - **Докстринг:** Сохраняет данные ответов в JSON-файл.
       **Аргументы:**
       `filepath` (str): Путь для сохранения файла.
       **Возвращает:**
       `bool`: True в случае успешного сохранения, иначе False.
     - **Параметры:**
       - `self`
       - `filepath: str`
     - **Тип возвращаемого значения:** `bool`
   ### `export_structured_conversation(self, structured_transcript: dict, reverse_chronological: bool = False) -> dict`
     - **Докстринг:** Экспортирует полные данные диалога на основе structured_transcript, используя локальную временную зону.
     - **Параметры:**
       - `self`
       - `structured_transcript: dict`
       - `reverse_chronological: bool` (по умолчанию: `False`)
     - **Тип возвращаемого значения:** `dict`
   ### `save_structured_conversation(self, filepath: str, structured_transcript: dict) -> bool`
     - **Докстринг:** Сохраняет структурированные данные диалога в JSON-файл.
       **Аргументы:**
       `filepath`: Путь для сохранения файла.
       `structured_transcript`: Структурированные записи диалога.
       **Возвращает:**
       `bool`: True в случае успешного сохранения, иначе False.
     - **Параметры:**
       - `self`
       - `filepath: str`
       - `structured_transcript: dict`
     - **Тип возвращаемого значения:** `bool`
   ### `create_response(self, question_time: datetime, question_text: str) -> str`
     - **Докстринг:** Создает запись ответа для нового вопроса, возвращает response_id.
     - **Параметры:**
       - `self`
       - `question_time: datetime`
       - `question_text: str`
     - **Тип возвращаемого значения:** `str`
   ### `update_response(self, response_id: str, response_text: str, is_complete: bool = False, is_incremental: bool = False)`
     - **Докстринг:** Обновляет содержимое ответа, поддерживает инкрементное обновление.
     - **Параметры:**
       - `self`
       - `response_id: str`
       - `response_text: str`
       - `is_complete: bool` (по умолчанию: `False`)
       - `is_incremental: bool` (по умолчанию: `False`)
     - **Тип возвращаемого значения:** `bool`
   ### `get_response(self, response_id: str) -> Optional[Response]`
     - **Докстринг:** Получает указанный ответ по его ID.
     - **Параметры:**
       - `self`
       - `response_id: str`
     - **Тип возвращаемого значения:** `Optional[Response]`
   ### `get_latest_response(self) -> Optional[Response]`
     - **Докстринг:** Получает самый последний ответ.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `Optional[Response]`
   ### `wait_for_new_response(self, timeout: Optional[float] = None) -> bool`
     - **Докстринг:** Ожидает нового полного ответа.
     - **Параметры:**
       - `self`
       - `timeout: Optional[float]` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `bool`

# Файл: src/SettingsManager.py

## Классы

## `SettingsManager`
 - **Докстринг:** Управляет сохранением и загрузкой настроек приложения.
 - **Методы:**
   ### `__init__(self)`
     - **Докстринг:** Инициализирует менеджер настроек.
     - **Параметры:**
       - `self`
   ### `_migrate_old_settings(self)`
     - **Докстринг:** Переносит файл настроек из старой версии.
     - **Параметры:**
       - `self`
   ### `load_settings(self) -> Dict[str, Any]`
     - **Докстринг:** Загружает настройки из файла.
       **Возвращает:**
       `Dict[str, Any]`: Словарь настроек.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `Dict[str, Any]`
   ### `save_settings(self, settings: Dict[str, Any]) -> bool`
     - **Докстринг:** Сохраняет настройки в файл.
       **Аргументы:**
       `settings`: Словарь настроек для сохранения.
       **Возвращает:**
       `bool`: True в случае успешного сохранения, иначе False.
     - **Параметры:**
       - `self`
       - `settings: Dict[str, Any]`
     - **Тип возвращаемого значения:** `bool`
   ### `get_setting(self, key: str) -> Any`
     - **Докстринг:** Получает значение указанной настройки.
       **Аргументы:**
       `key`: Имя ключа настройки.
       **Возвращает:**
       `Any`: Значение настройки, или значение по умолчанию, если ключ не найден.
     - **Параметры:**
       - `self`
       - `key: str`
     - **Тип возвращаемого значения:** `Any`
   ### `update_setting(self, key: str, value: Any) -> bool`
     - **Докстринг:** Обновляет значение указанной настройки.
       **Аргументы:**
       `key`: Имя ключа настройки.
       `value`: Новое значение настройки.
       **Возвращает:**
       `bool`: True в случае успешного обновления, иначе False.
     - **Параметры:**
       - `self`
       - `key: str`
       - `value: Any`
     - **Тип возвращаемого значения:** `bool`
   ### `debug_mode(self) -> bool` (property)
     - **Докстринг:** Включен ли режим отладки.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `bool`

# Файл: src/TemplateManager.py
 - **Докстринг модуля:** 
   ```
   src/template_manager.py
   Класс для управления системными ролями и шаблонами, отвечает за загрузку, обновление и поддержку шаблонов.
   ```

## Классы

## `TemplateManager`
 - **Докстринг:** Класс менеджера шаблонов, обрабатывает файлы шаблонов, связанные с системными ролями.
 - **Методы:**
   ### `_get_template_paths(cls) -> Dict[str, Tuple[str, str]]` (classmethod)
     - **Докстринг:** Получает конфигурацию путей к шаблонам.
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `Dict[str, Tuple[str, str]]`
   ### `initialize_default_role(cls) -> bool` (classmethod)
     - **Докстринг:** Инициализирует системную роль по умолчанию.
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `bool`
   ### `load_template(cls, filepath: str) -> str` (classmethod)
     - **Докстринг:** Загружает содержимое файла шаблона.
     - **Параметры:**
       - `cls`
       - `filepath: str`
     - **Тип возвращаемого значения:** `str`
   ### `get_template_files(cls, category: str) -> List[str]` (classmethod)
     - **Докстринг:** Получает все файлы шаблонов указанной категории.
     - **Параметры:**
       - `cls`
       - `category: str`
     - **Тип возвращаемого значения:** `List[str]`
   ### `update_system_role(cls, system_role_file: str, case_detail_file: str, knowledge_file: str) -> Optional[str]` (classmethod)
     - **Докстринг:** Обновляет конфигурацию системной роли.
     - **Параметры:**
       - `cls`
       - `system_role_file: str`
       - `case_detail_file: str`
       - `knowledge_file: str`
     - **Тип возвращаемого значения:** `Optional[str]`
   ### `ensure_template_directories(cls) -> None` (classmethod)
     - **Докстринг:** Гарантирует существование всех каталогов шаблонов.
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `None`
   ### `get_current_role(cls) -> Optional[str]` (classmethod)
     - **Докстринг:** Получает текущую конфигурацию системной роли.
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `Optional[str]`

# Файл: src/TranscriberModels.py

## Функции

### `get_model(use_api: bool)`
 - **Докстринг:** Возвращает экземпляр транскрибатора в зависимости от флага `use_api`.
   **Аргументы:**
   `use_api` (bool): Если `True`, возвращает `APIWhisperTranscriber`, иначе `FunASRTranscriber`.
   **Возвращает:**
   `Union[APIWhisperTranscriber, FunASRTranscriber]`: Экземпляр транскрибатора.
 - **Параметры:**
   - `use_api: bool`
 - **Тип возвращаемого значения:** `Union[APIWhisperTranscriber, FunASRTranscriber]`

## Классы

## `FunASRTranscriber`
 - **Докстринг:** Класс для транскрибации аудио с использованием FunASR.
 - **Методы:**
   ### `__init__(self)`
     - **Параметры:**
       - `self`
   ### `init_asr(self) -> ASRInterface`
     - **Докстринг:** Инициализирует и возвращает систему ASR на основе конфигурации.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `ASRInterface`
   ### `get_transcription(self, wav_file_path: str) -> str`
     - **Докстринг:** Получает транскрипцию для указанного WAV-файла.
       **Аргументы:**
       `wav_file_path` (str): Путь к WAV-файлу.
       **Возвращает:**
       `str`: Транскрибированный текст или пустая строка в случае ошибки.
     - **Параметры:**
       - `self`
       - `wav_file_path: str`
     - **Тип возвращаемого значения:** `str`

## `WhisperTranscriber`
 - **Докстринг:** Класс для транскрибации аудио с использованием Whisper. (В данный момент этот класс, похоже, не используется активно в пользу FunASR или API)
 - **Методы:**
   ### `__init__(self)`
     - **Параметры:**
       - `self`
   ### `get_transcription(self, wav_file_path: str) -> str`
     - **Докстринг:** Получает транскрипцию для указанного WAV-файла с использованием Whisper.
       **Аргументы:**
       `wav_file_path` (str): Путь к WAV-файлу.
       **Возвращает:**
       `str`: Транскрибированный текст или пустая строка в случае ошибки.
     - **Параметры:**
       - `self`
       - `wav_file_path: str`
     - **Тип возвращаемого значения:** `str`

## `APIWhisperTranscriber`
 - **Докстринг:** Класс для транскрибации аудио с использованием OpenAI Whisper API.
 - **Методы:**
   ### `get_transcription(self, wav_file_path: str) -> str`
     - **Докстринг:** Получает транскрипцию для указанного WAV-файла через OpenAI API.
       **Аргументы:**
       `wav_file_path` (str): Путь к WAV-файлу.
       **Возвращает:**
       `str`: Транскрибированный текст или пустая строка в случае ошибки.
     - **Параметры:**
       - `self`
       - `wav_file_path: str`
     - **Тип возвращаемого значения:** `str`

# Файл: src/TranscriptUI.py

## Классы

## `TranscriptUI`
 - **Докстринг:** Обрабатывает отображение и взаимодействие с UI записей диалога.
 - **Методы:**
   ### `__init__(self, textbox: ctk.CTkTextbox, response_manager: Any)`
     - **Докстринг:** Инициализирует TranscriptUI.
       **Аргументы:**
       `textbox`: `CTkTextbox` для отображения записей диалога.
       `response_manager`: Экземпляр `ResponseManager` для управления ответами на диалоги.
     - **Параметры:**
       - `self`
       - `textbox: ctk.CTkTextbox`
       - `response_manager: Any`
   ### `_initialize_default_lines(self) -> None`
     - **Докстринг:** Инициализирует строки по умолчанию для Говорящего и Вас.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `None`
   ### `_configure_textbox(self) -> None`
     - **Докстринг:** Конфигурирует основные настройки текстового поля.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `None`
   ### `toggle_debug(self, enabled: bool = None) -> None`
     - **Докстринг:** Переключает режим отладки.
       **Аргументы:**
       `enabled`: Если предоставлено, напрямую устанавливает состояние режима отладки; если не предоставлено, переключает текущее состояние.
     - **Параметры:**
       - `self`
       - `enabled: bool` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `None`
   ### `update_transcript(self, transcriber: Any) -> None`
     - **Докстринг:** Обновляет отображение записей диалога (потоковое обновление).
       **Аргументы:**
       `transcriber`: Экземпляр `AudioTranscriber`, содержащий данные записей диалога.
     - **Параметры:**
       - `self`
       - `transcriber: Any`
     - **Тип возвращаемого значения:** `None`
   ### `_get_new_records(self, transcriber: Any) -> List[Dict]`
     - **Докстринг:** Получает новые записи диалога, включая новые и обновленные существующие записи.
       **Аргументы:**
       `transcriber`: Экземпляр `AudioTranscriber`.
       **Возвращает:**
       `List[Dict]`: Список новых и обновленных записей.
     - **Параметры:**
       - `self`
       - `transcriber: Any`
     - **Тип возвращаемого значения:** `List[Dict]`
   ### `_append_new_records(self, records: List[Dict]) -> None`
     - **Докстринг:** Добавляет новые записи в текстовое поле.
     - **Параметры:**
       - `self`
       - `records: List[Dict]`
     - **Тип возвращаемого значения:** `None`
   ### `_add_record_tags(self, position: str, record: Dict) -> None`
     - **Докстринг:** Добавляет тег и интерактивность к записи.
     - **Параметры:**
       - `self`
       - `position: str`
       - `record: Dict`
     - **Тип возвращаемого значения:** `None`
   ### `_add_record_tags_(self, position: str, record: Dict) -> None`
     - **Докстринг:** Добавляет тег и интерактивность к записи. (Дублирующий метод, возможно, для отладки)
       **Аргументы:**
       `position`: Позиция вставки.
       `record`: Данные записи.
     - **Параметры:**
       - `self`
       - `position: str`
       - `record: Dict`
     - **Тип возвращаемого значения:** `None`
   ### `_update_response_text_(self, response_text: str) -> None`
     - **Докстринг:** Обновляет содержимое текстового поля ответа. (Дублирующий метод)
     - **Параметры:**
       - `self`
       - `response_text: str`
     - **Тип возвращаемого значения:** `None`
   ### `_update_response_text(self, response_text: str, question_text: str = None) -> None`
     - **Докстринг:** Обновляет содержимое текстового поля ответа, включая вопрос и ответ.
       **Аргументы:**
       `response_text`: Текст ответа.
       `question_text`: Связанный текст вопроса.
     - **Параметры:**
       - `self`
       - `response_text: str`
       - `question_text: str` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `None`
   ### `_format_response_display(self, question_text: Optional[str], response_text: str) -> str`
     - **Докстринг:** Форматирует отображение вопроса и ответа.
       **Аргументы:**
       `question_text`: Текст вопроса.
       `response_text`: Текст ответа.
       **Возвращает:**
       `str`: Отформатированный текст для отображения.
     - **Параметры:**
       - `self`
       - `question_text: Optional[str]`
       - `response_text: str`
     - **Тип возвращаемого значения:** `str`
   ### `clear(self) -> None`
     - **Докстринг:** Очищает все содержимое и счетчики.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `None`
   ### `_on_response_update(self, response_id: str, response_text: str, is_complete: bool) -> None`
     - **Докстринг:** Обратный вызов для обновления ответа.
       **Аргументы:**
       `response_id`: ID ответа.
       `response_text`: Обновленный текст ответа.
       `is_complete`: Завершен ли ответ.
     - **Параметры:**
       - `self`
       - `response_id: str`
       - `response_text: str`
       - `is_complete: bool`
     - **Тип возвращаемого значения:** `None`
   ### `update_latest_response(self, response_id: str, response_text: str, question_text: str = None) -> None`
     - **Докстринг:** Принудительно обновляет текст последнего ответа, независимо от состояния блокировки.
     - **Параметры:**
       - `self`
       - `response_id: str`
       - `response_text: str`
       - `question_text: str` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `None`
   ### `add_click_handler(self, response_textbox: ctk.CTkTextbox) -> None`
     - **Докстринг:** Добавляет обработчик событий клика.
     - **Параметры:**
       - `self`
       - `response_textbox: ctk.CTkTextbox`
     - **Тип возвращаемого значения:** `None`
   ### `is_response_frozen(self) -> bool`
     - **Докстринг:** Проверяет, заблокирован ли ответ.
       **Возвращает:**
       `bool`: True, если ответ заблокирован, иначе False.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `bool`

# Файл: src/asr/asr_factory.py

## Классы

## `ASRFactory`
 - **Докстринг:** Фабрика для создания экземпляров систем распознавания речи (ASR).
 - **Методы:**
   ### `get_asr_system(system_name: str, **kwargs) -> Type[ASRInterface]` (staticmethod)
     - **Докстринг:** Получает экземпляр указанной системы ASR.
       **Аргументы:**
       `system_name` (str): Название системы ASR (например, "Faster-Whisper", "FunASR").
       `**kwargs`: Аргументы, специфичные для конкретной системы ASR.
       **Возвращает:**
       `Type[ASRInterface]`: Экземпляр класса, реализующего интерфейс `ASRInterface`.
       **Вызывает исключение:**
       `ValueError`: Если указано неизвестное имя системы ASR.
     - **Параметры:**
       - `system_name: str`
       - `**kwargs`
     - **Тип возвращаемого значения:** `Type[ASRInterface]`

# Файл: src/asr/asr_interface.py

## Классы

## `ASRInterface(metaclass=abc.ABCMeta)`
 - **Докстринг:** Абстрактный базовый класс (интерфейс) для систем распознавания речи (ASR).
 - **Методы:**
   ### `transcribe_with_local_vad(self) -> str` (abstractmethod)
     - **Докстринг:** Активирует микрофон на этом устройстве, транскрибирует аудио при обнаружении паузы в речи с использованием VAD (Voice Activity Detection) и возвращает транскрипцию. Этот метод должен блокироваться до тех пор, пока не будет доступна транскрипция.
       **Возвращает:**
       `str`: Транскрипция речевого аудио.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_np(self, audio: np.ndarray) -> str` (abstractmethod)
     - **Докстринг:** Транскрибирует речевое аудио в формате массива numpy и возвращает транскрипцию.
       **Аргументы:**
       `audio` (np.ndarray): Массив numpy с аудиоданными для транскрибации.
       **Возвращает:**
       `str`: Транскрибированный текст.
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_wav(self, audio_path: str) -> str` (abstractmethod)
     - **Докстринг:** Транскрибирует речевое аудио из WAV-файла и возвращает транскрипцию.
       **Аргументы:**
       `audio_path` (str): Путь к WAV-файлу для транскрибации.
       **Возвращает:**
       `str`: Транскрибированный текст.
     - **Параметры:**
       - `self`
       - `audio_path: str`
     - **Тип возвращаемого значения:** `str`

# Файл: src/asr/asr_with_vad.py
 - **Докстринг модуля:** (Лицензия и уведомление об авторских правах опущены для краткости)

## Классы

## `VoiceRecognitionVAD`
 - **Докстринг:** Класс для распознавания голоса с использованием детекции голосовой активности (VAD).
 - **Методы:**
   ### `__init__(self, asr_transcribe_func: Callable, wake_word: str | None = None, function: Callable = print) -> None`
     - **Докстринг:** Инициализирует класс `VoiceRecognition`, настраивая необходимые модели, потоки и очереди... (сокращено)
     - **Параметры:**
       - `self`
       - `asr_transcribe_func: Callable`
       - `wake_word: str | None` (по умолчанию: `None`)
       - `function: Callable` (по умолчанию: `print`)
     - **Тип возвращаемого значения:** `None`
   ### `_setup_audio_stream(self)`
     - **Докстринг:** Настраивает входной аудиопоток с использованием `sounddevice`.
     - **Параметры:**
       - `self`
   ### `_setup_vad_model(self)`
     - **Докстринг:** Загружает модель детекции голосовой активности (VAD).
     - **Параметры:**
       - `self`
   ### `audio_callback(self, indata, frames, time, status)`
     - **Докстринг:** Функция обратного вызова для аудиопотока, обрабатывающая входящие данные.
     - **Параметры:**
       - `self`
       - `indata`
       - `frames`
       - `time`
       - `status`
   ### `start(self)`
     - **Докстринг:** Запускает голосового ассистента, непрерывно прослушивая входной сигнал и отвечая. (Этот метод, похоже, предназначен для непрерывной работы с кодовым словом)
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** (неявно `None` или результат `_listen_and_respond`)
   ### `start_listening(self) -> str`
     - **Докстринг:** Начинает прослушивание аудиовхода и соответствующим образом реагирует при обнаружении активного голоса. Эта функция вернет транскрибированный текст после обнаружения паузы. Она использует функцию `transcribe`, предоставленную в конструкторе, для транскрибации аудио.
       **Возвращает:**
       `str`: Транскрибированный текст.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `_listen_and_respond(self, returnText=False)`
     - **Докстринг:** Прослушивает аудиовход и соответствующим образом реагирует при обнаружении кодового слова (если установлено). Если `returnText=True`, возвращает транскрибированный текст.
     - **Параметры:**
       - `self`
       - `returnText` (по умолчанию: `False`)
     - **Тип возвращаемого значения:** (`str` или `None`)
   ### `_handle_audio_sample(self, sample, vad_confidence)`
     - **Докстринг:** Обрабатывает каждый аудиосемпл.
     - **Параметры:**
       - `self`
       - `sample`
       - `vad_confidence`
     - **Тип возвращаемого значения:** (`str` или `None`)
   ### `_manage_pre_activation_buffer(self, sample, vad_confidence)`
     - **Докстринг:** Управляет буфером аудиосемплов до активации (т.е. до обнаружения голоса).
     - **Параметры:**
       - `self`
       - `sample`
       - `vad_confidence`
   ### `_process_activated_audio(self, sample: np.ndarray, vad_confidence: bool)`
     - **Докстринг:** Обрабатывает аудиосемплы после активации (т.е. после обнаружения кодового слова или начала речи). Использует лимит паузы для определения момента обработки обнаруженного аудио. Это делается для того, чтобы гарантировать захват всего предложения перед обработкой, включая небольшие паузы.
     - **Параметры:**
       - `self`
       - `sample: np.ndarray`
       - `vad_confidence: bool`
     - **Тип возвращаемого значения:** (`str` или `None`)
   ### `_process_detected_audio(self)`
     - **Докстринг:** Обрабатывает обнаруженное аудио и генерирует ответ (транскрипцию).
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** (`str` или `None`)
   ### `asr(self, samples: List[np.ndarray]) -> str`
     - **Докстринг:** Выполняет автоматическое распознавание речи на собранных семплах.
     - **Параметры:**
       - `self`
       - `samples: List[np.ndarray]`
     - **Тип возвращаемого значения:** `str`
   ### `reset(self)`
     - **Докстринг:** Сбрасывает состояние записи и очищает буферы.
     - **Параметры:**
       - `self`

# Файл: src/asr/azure_asr.py

## Классы

## `VoiceRecognition(ASRInterface)`
 - **Докстринг:** Класс для распознавания речи с использованием Azure Cognitive Speech Services.
 - **Методы:**
   ### `__init__(self, subscription_key=os.getenv("AZURE_API_Key"), region=os.getenv("AZURE_REGION"), callback: Callable = print)`
     - **Докстринг:** Инициализирует объект `VoiceRecognition`.
       **Аргументы:**
       `subscription_key` (str, optional): Ключ подписки Azure. По умолчанию получается из переменной окружения `AZURE_API_Key`.
       `region` (str, optional): Регион Azure. По умолчанию получается из переменной окружения `AZURE_REGION`.
       `callback` (Callable, optional): Функция обратного вызова, вызываемая с распознанным текстом. По умолчанию `print`.
     - **Параметры:**
       - `self`
       - `subscription_key` (по умолчанию: `os.getenv("AZURE_API_Key")`)
       - `region` (по умолчанию: `os.getenv("AZURE_REGION")`)
       - `callback: Callable` (по умолчанию: `print`)
   ### `_create_speech_recognizer(self, uses_default_microphone: bool = True) -> speechsdk.SpeechRecognizer`
     - **Докстринг:** Создает и возвращает объект `SpeechRecognizer`.
       **Аргументы:**
       `uses_default_microphone` (bool, optional): Использовать ли микрофон по умолчанию. По умолчанию `True`.
       **Возвращает:**
       `speechsdk.SpeechRecognizer`: Объект распознавателя речи.
     - **Параметры:**
       - `self`
       - `uses_default_microphone: bool` (по умолчанию: `True`)
     - **Тип возвращаемого значения:** `speechsdk.SpeechRecognizer`
   ### `transcribe_with_local_vad(self) -> str`
     - **Докстринг:** Транскрибирует речь с использованием локального VAD (Voice Activity Detection). Примечание: Azure SDK обычно имеет встроенный VAD, поэтому этот метод может быть упрощен.
       **Возвращает:**
       `str`: Распознанный текст или пустая строка в случае неудачи.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_np(self, audio: np.ndarray) -> str`
     - **Докстринг:** Транскрибирует аудиоданные из массива numpy.
       **Аргументы:**
       `audio` (np.ndarray): Массив numpy с аудиоданными для транскрибации.
       **Возвращает:**
       `str`: Распознанный текст или результат операции распознавания. (Примечание: возвращает объект результата, а не только текст)
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `str`

# Файл: src/asr/faster_whisper_asr.py

## Классы

## `VoiceRecognition(ASRInterface)`
 - **Докстринг:** Класс для распознавания речи с использованием модели Faster Whisper.
 - **Методы:**
   ### `__init__(self, model_path: str = "distil-medium.en", download_root: str = None, language: str = "en", device: str = "auto") -> None`
     - **Докстринг:** Инициализирует объект `VoiceRecognition`.
       **Аргументы:**
       `model_path` (str, optional): Путь к локальной модели или имя модели для загрузки. По умолчанию `"distil-medium.en"`.
       `download_root` (str, optional): Каталог для загрузки модели. По умолчанию `None` (используется каталог кэша faster-whisper).
       `language` (str, optional): Язык распознавания (например, "en", "ru"). По умолчанию `"en"`.
       `device` (str, optional): Устройство для выполнения модели ("auto", "cpu", "cuda"). По умолчанию `"auto"`.
     - **Параметры:**
       - `self`
       - `model_path: str` (по умолчанию: `"distil-medium.en"`)
       - `download_root: str` (по умолчанию: `None`)
       - `language: str` (по умолчанию: `"en"`)
       - `device: str` (по умолчанию: `"auto"`)
     - **Тип возвращаемого значения:** `None`
   ### `transcribe_with_local_vad(self) -> str`
     - **Докстринг:** Транскрибирует аудио с использованием локальной детекции голосовой активности (VAD).
       **Возвращает:**
       `str`: Распознанный текст.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_np(self, audio: np.ndarray) -> str`
     - **Докстринг:** Транскрибирует аудиоданные из массива numpy.
       **Аргументы:**
       `audio` (np.ndarray): Массив numpy с аудиоданными для транскрибации.
       **Возвращает:**
       `str`: Распознанный текст или пустая строка, если ничего не распознано.
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `str`

# Файл: src/asr/fun_asr.py

## Классы

## `VoiceRecognition(ASRInterface)`
 - **Докстринг:** Класс для распознавания речи с использованием моделей FunASR.
 - **Методы:**
   ### `__init__(self, model_name: str = "iic/SenseVoiceSmall", language: str = "auto", vad_model = None, punc_model=None, ncpu: int = None, hub: str = None, device: str = "cpu", sample_rate: int = 16000, use_itn: bool = False) -> None`
     - **Докстринг:** Инициализирует объект `VoiceRecognition` для FunASR.
       **Аргументы:**
       `model_name` (str, optional): Имя или путь к модели FunASR. По умолчанию `"iic/SenseVoiceSmall"`.
       `language` (str, optional): Язык для распознавания. По умолчанию `"auto"`.
       `vad_model` (str, optional): Имя или путь к модели VAD. По умолчанию `None`.
       `punc_model` (str, optional): Имя или путь к модели пунктуации. По умолчанию `None`.
       `ncpu` (int, optional): Количество ядер CPU. По умолчанию определяется библиотекой.
       `hub` (str, optional): Хаб для загрузки моделей. По умолчанию `None`.
       `device` (str, optional): Устройство для вычислений. По умолчанию `"cpu"`.
       `sample_rate` (int, optional): Ожидаемая частота дискретизации. По умолчанию `16000`.
       `use_itn` (bool, optional): Использовать ли инверсную нормализацию текста. По умолчанию `False`.
     - **Параметры:**
       - `self`
       - `model_name: str` (по умолчанию: `"iic/SenseVoiceSmall"`)
       - `language: str` (по умолчанию: `"auto"`)
       - `vad_model` (по умолчанию: `None`)
       - `punc_model` (по умолчанию: `None`)
       - `ncpu: int` (по умолчанию: `None`)
       - `hub: str` (по умолчанию: `None`)
       - `device: str` (по умолчанию: `"cpu"`)
       - `sample_rate: int` (по умолчанию: `16000`)
       - `use_itn: bool` (по умолчанию: `False`)
     - **Тип возвращаемого значения:** `None`
   ### `transcribe_with_local_vad(self) -> str`
     - **Докстринг:** Транскрибирует аудио с использованием локальной детекции голосовой активности (VAD).
       **Возвращает:**
       `str`: Распознанный текст.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_wav(self, audio_path: str) -> str`
     - **Докстринг:** Транскрибирует аудио из WAV-файла.
       **Аргументы:**
       `audio_path` (str): Путь к WAV-файлу.
       **Возвращает:**
       `str`: Распознанный текст или пустая строка в случае ошибки.
     - **Параметры:**
       - `self`
       - `audio_path: str`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_np(self, audio: np.ndarray) -> str`
     - **Докстринг:** Транскрибирует аудиоданные из массива numpy.
       **Аргументы:**
       `audio` (np.ndarray): Массив numpy с аудиоданными для транскрибации.
       **Возвращает:**
       `str`: Распознанный текст или пустая строка в случае ошибки.
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `str`
   ### `_numpy_to_wav_in_memory(self, numpy_array: np.ndarray, sample_rate: int) -> io.BytesIO`
     - **Докстринг:** Преобразует массив numpy в WAV-формат в памяти.
       **Аргументы:**
       `numpy_array` (np.ndarray): Аудиоданные в виде массива numpy.
       `sample_rate` (int): Частота дискретизации.
       **Возвращает:**
       `io.BytesIO`: Объект `BytesIO`, содержащий аудиоданные в формате WAV.
     - **Параметры:**
       - `self`
       - `numpy_array: np.ndarray`
       - `sample_rate: int`
     - **Тип возвращаемого значения:** `io.BytesIO`

# Файл: src/asr/openai_whisper_asr.py

## Классы

## `VoiceRecognition(ASRInterface)`
 - **Докстринг:** Класс для распознавания речи с использованием стандартной библиотеки OpenAI Whisper.
 - **Методы:**
   ### `__init__(self, name: str = "base", download_root: str = None, device="cpu") -> None`
     - **Докстринг:** Инициализирует объект `VoiceRecognition` для OpenAI Whisper.
       **Аргументы:**
       `name` (str, optional): Имя модели Whisper. По умолчанию `"base"`.
       `download_root` (str, optional): Каталог для загрузки модели. По умолчанию `None` (используется каталог по умолчанию Whisper).
       `device` (str, optional): Устройство для выполнения модели. По умолчанию `"cpu"`.
     - **Параметры:**
       - `self`
       - `name: str` (по умолчанию: `"base"`)
       - `download_root: str` (по умолчанию: `None`)
       - `device` (по умолчанию: `"cpu"`)
     - **Тип возвращаемого значения:** `None`
   ### `transcribe_with_local_vad(self) -> str`
     - **Докстринг:** Транскрибирует аудио с использованием локальной детекции голосовой активности (VAD).
       **Возвращает:**
       `str`: Распознанный текст.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_np(self, audio: np.ndarray) -> str`
     - **Докстринг:** Транскрибирует аудиоданные из массива numpy.
       **Аргументы:**
       `audio` (np.ndarray): Массив numpy с аудиоданными для транскрибации.
       **Возвращает:**
       `str`: Распознанный текст.
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `str`

# Файл: src/asr/vad.py
 - **Докстринг модуля:** (Лицензия и уведомление об авторских правах опущены для краткости)

## Классы

## `VAD`
 - **Докстринг:** Класс для детекции голосовой активности (VAD) с использованием модели ONNX.
 - **Методы:**
   ### `__init__(self, model_path: str, window_size_samples: int = int(SAMPLE_RATE / 10))`
     - **Докстринг:** Инициализирует объект VAD.
       **Аргументы:**
       `model_path` (str): Путь к файлу модели VAD в формате ONNX.
       `window_size_samples` (int, optional): Размер окна в семплах для обработки. По умолчанию равен `SAMPLE_RATE / 10` (100 мс при 16 кГц).
     - **Параметры:**
       - `self`
       - `model_path: str`
       - `window_size_samples: int` (по умолчанию: `int(SAMPLE_RATE / 10)`)
   ### `reset(self)`
     - **Докстринг:** Сбрасывает внутренние состояния (h и c) модели к начальным значениям.
     - **Параметры:**
       - `self`
   ### `process_chunk(self, chunk: np.ndarray) -> np.ndarray`
     - **Докстринг:** Обрабатывает один чанк (фрагмент) аудиоданных.
       **Аргументы:**
       `chunk` (np.ndarray): Аудиочанк в виде массива numpy.
       **Возвращает:**
       `np.ndarray`: Результат детекции VAD для этого чанка (обычно вероятность наличия голоса).
     - **Параметры:**
       - `self`
       - `chunk: np.ndarray`
     - **Тип возвращаемого значения:** `np.ndarray`
   ### `process_file(self, audio: np.ndarray) -> np.ndarray`
     - **Докстринг:** Обрабатывает весь аудиофайл (представленный как массив numpy) по чанкам.
       **Аргументы:**
       `audio` (np.ndarray): Аудиоданные всего файла.
       **Возвращает:**
       `np.ndarray`: Массив результатов детекции VAD для каждого чанка.
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `np.ndarray`

# Файл: src/asr/whisper_cpp_asr.py

## Классы

## `VoiceRecognition(ASRInterface)`
 - **Докстринг:** Класс для распознавания речи с использованием Whisper.cpp.
 - **Методы:**
   ### `__init__(self, model_name: str = "base", model_dir="asr/models", language: str = "en", print_realtime: bool = False, print_progress: bool = False, **kwargs) -> None`
     - **Докстринг:** Инициализирует объект `VoiceRecognition` для Whisper.cpp.
       **Аргументы:**
       `model_name` (str, optional): Имя или путь к модели. По умолчанию `"base"`.
       `model_dir` (str, optional): Каталог моделей. По умолчанию `"asr/models"`.
       `language` (str, optional): Язык. По умолчанию `"en"`.
       `print_realtime` (bool, optional): Печать в реальном времени. По умолчанию `False`.
       `print_progress` (bool, optional): Печать прогресса. По умолчанию `False`.
       `**kwargs`: Дополнительные аргументы, передаваемые в конструктор `pywhispercpp.model.Model`.
     - **Параметры:**
       - `self`
       - `model_name: str` (по умолчанию: `"base"`)
       - `model_dir` (по умолчанию: `"asr/models"`)
       - `language: str` (по умолчанию: `"en"`)
       - `print_realtime: bool` (по умолчанию: `False`)
       - `print_progress: bool` (по умолчанию: `False`)
       - `**kwargs`
     - **Тип возвращаемого значения:** `None`
   ### `transcribe_with_local_vad(self) -> str`
     - **Докстринг:** Транскрибирует аудио с использованием локальной детекции голосовой активности (VAD).
       **Возвращает:**
       `str`: Распознанный текст.
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `transcribe_np(self, audio: np.ndarray) -> str`
     - **Докстринг:** Транскрибирует аудиоданные из массива numpy.
       **Аргументы:**
       `audio` (np.ndarray): Массив numpy с аудиоданными для транскрибации.
       **Возвращает:**
       `str`: Распознанный текст.
     - **Параметры:**
       - `self`
       - `audio: np.ndarray`
     - **Тип возвращаемого значения:** `str`

# Файл: src/config.py

## Классы

## `PathConfig`
 - **Докстринг:** Управление конфигурацией путей
 - **Методы:**
   ### `get_project_root()` (staticmethod)
     - **Докстринг:** Получить корневой каталог проекта
     - **Тип возвращаемого значения:** `str`
   ### `get_resource_path()` (staticmethod)
     - **Докстринг:** Получить каталог файлов ресурсов
     - **Тип возвращаемого значения:** `str`
   ### `get_config_path()` (staticmethod)
     - **Докстринг:** Получить каталог конфигурационных файлов
     - **Тип возвращаемого значения:** `str`
   ### `get_prompt_path()` (staticmethod)
     - **Докстринг:** Получить каталог для prompt'ов
     - **Тип возвращаемого значения:** `str`
   ### `get_templates_path()` (staticmethod)
     - **Докстринг:** Получить каталог шаблонов
     - **Тип возвращаемого значения:** `str`
   ### `get_models_path()` (staticmethod)
     - **Докстринг:** Получить каталог файлов моделей
     - **Тип возвращаемого значения:** `str`

## `EnvConfig`
 - **Докстринг:** Класс управления конфигурацией окружения
 - **Методы:**
   ### `__new__(cls)`
   ### `initialize(cls) -> None` (classmethod)
     - **Докстринг:** Инициализировать конфигурацию окружения
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `None`
   ### `create_env_template(cls, env_path: str) -> None` (classmethod)
     - **Докстринг:** Создать шаблон файла .env
     - **Параметры:**
       - `cls`
       - `env_path: str`
     - **Тип возвращаемого значения:** `None`
   ### `get_openai_key(cls) -> Optional[str]` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `Optional[str]`
   ### `get_llm_provider(cls) -> str` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `str`
   ### `get_llm_api_base_url(cls) -> Optional[str]` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `Optional[str]`
   ### `get_llm_model_name(cls) -> str` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `str`
   ### `ensure_api_key(cls) -> bool` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `bool`

## `SystemConfig`
 - **Методы:**
   ### `get_system_role(cls)` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `str`
   ### `set_system_role(cls, role)` (classmethod)
     - **Параметры:**
       - `cls`
       - `role`
   ### `get_record_only_mode(cls)` (classmethod)
     - **Докстринг:** Получить текущее состояние режима 'только запись'
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `bool`
   ### `set_record_only_mode(cls, value: bool)` (classmethod)
     - **Докстринг:** Установить состояние режима 'только запись'
       **Аргументы:**
       `value` (bool): True для включения режима 'только запись', False для выключения
     - **Параметры:**
       - `cls`
       - `value: bool`

## `AudioConfig`
 - **Методы:**
   ### `get_buffer_chunks(cls)` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `int`
   ### `set_buffer_chunks(cls, value)` (classmethod)
     - **Параметры:**
       - `cls`
       - `value`
     - **Тип возвращаемого значения:** `bool`
   ### `get_phrase_timeout(cls)` (classmethod)
     - **Параметры:**
       - `cls`
     - **Тип возвращаемого значения:** `float`
   ### `set_phrase_timeout(cls, value)` (classmethod)
     - **Параметры:**
       - `cls`
       - `value`
     - **Тип возвращаемого значения:** `bool`

# Файл: src/custom_speech_recognition/__init__.py
 - **Докстринг модуля:** Библиотека для выполнения распознавания речи с поддержкой нескольких движков и API, онлайн и офлайн.

## Классы

## `AudioSource(object)`
 - **Докстринг:** Абстрактный класс, представляющий источник аудио.
 - **Методы:**
   ### `__init__(self)`
   ### `__enter__(self)`
   ### `__exit__(self, exc_type, exc_value, traceback)`

## `Microphone(AudioSource)`
 - **Докстринг:** Создает новый экземпляр ``Microphone``, представляющий физический микрофон на компьютере... (сокращено)
 - **Методы:**
   ### `__init__(self, device_index=None, sample_rate=None, chunk_size=1024, speaker=False, channels = 1)`
     - **Параметры:**
       - `self`
       - `device_index` (по умолчанию: `None`)
       - `sample_rate` (по умолчанию: `None`)
       - `chunk_size` (по умолчанию: `1024`)
       - `speaker` (по умолчанию: `False`)
       - `channels` (по умолчанию: `1`)
   ### `get_pyaudio()` (staticmethod)
     - **Докстринг:** Импортирует модуль `pyaudio` и проверяет его версию. Вызывает исключения, если `pyaudio` не найден или установлена неправильная версия.
     - **Тип возвращаемого значения:** `module`
   ### `list_microphone_names()` (staticmethod)
     - **Докстринг:** Возвращает список имен всех доступных микрофонов...
     - **Тип возвращаемого значения:** `list`
   ### `list_working_microphones()` (staticmethod)
     - **Докстринг:** Возвращает словарь, сопоставляющий индексы устройств с именами микрофонов, для микрофонов, которые в данный момент улавливают звуки...
     - **Тип возвращаемого значения:** `dict`
   ### `__enter__(self)`
     - **Тип возвращаемого значения:** `self`
   ### `__exit__(self, exc_type, exc_value, traceback)`

## `Microphone.MicrophoneStream(object)`
 - **Докстринг:** Внутренний класс-оболочка для потока PyAudio.
 - **Методы:**
   ### `__init__(self, pyaudio_stream)`
     - **Параметры:**
       - `self`
       - `pyaudio_stream`
   ### `read(self, size)`
     - **Параметры:**
       - `self`
       - `size`
     - **Тип возвращаемого значения:** `bytes`
   ### `close(self)`
     - **Параметры:**
       - `self`

## `AudioFile(AudioSource)`
 - **Докстринг:** Создает новый экземпляр ``AudioFile`` из аудиофайла WAV/AIFF/FLAC ``filename_or_fileobject``... (сокращено)
 - **Методы:**
   ### `__init__(self, filename_or_fileobject)`
     - **Параметры:**
       - `self`
       - `filename_or_fileobject`
   ### `__enter__(self)`
     - **Тип возвращаемого значения:** `self`
   ### `__exit__(self, exc_type, exc_value, traceback)`

## `AudioFile.AudioFileStream(object)`
 - **Докстринг:** Внутренний класс-оболочка для потока аудиофайла.
 - **Методы:**
   ### `__init__(self, audio_reader, little_endian, samples_24_bit_pretending_to_be_32_bit)`
     - **Параметры:**
       - `self`
       - `audio_reader`
       - `little_endian`
       - `samples_24_bit_pretending_to_be_32_bit`
   ### `read(self, size=-1)`
     - **Параметры:**
       - `self`
       - `size` (по умолчанию: `-1`)
     - **Тип возвращаемого значения:** `bytes`

## `Recognizer(AudioSource)`
 - **Докстринг:** Класс `Recognizer` представляет собой набор функций для распознавания речи.
 - **Методы:**
   ### `__init__(self)`
     - **Докстринг:** Создает новый экземпляр ``Recognizer``, который представляет собой набор функций распознавания речи.
   ### `record(self, source, duration=None, offset=None)`
     - **Докстринг:** Записывает до ``duration`` секунд аудио из ``source`` (экземпляр ``AudioSource``)...
     - **Параметры:**
       - `self`
       - `source`
       - `duration` (по умолчанию: `None`)
       - `offset` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `AudioData`
   ### `adjust_for_ambient_noise(self, source, duration=1)`
     - **Докстринг:** Динамически настраивает порог энергии, используя аудио из ``source``...
     - **Параметры:**
       - `self`
       - `source`
       - `duration` (по умолчанию: `1`)
   ### `snowboy_wait_for_hot_word(self, snowboy_location, snowboy_hot_word_files, source, timeout=None)`
     - **Докстринг:** Ожидает произнесения кодового слова с использованием Snowboy.
     - **Параметры:**
       - `self`
       - `snowboy_location`
       - `snowboy_hot_word_files`
       - `source`
       - `timeout` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `tuple` (`bytes`, `float`)
   ### `listen(self, source, timeout=None, phrase_time_limit=None, snowboy_configuration=None, stream=False)`
     - **Докстринг:** Записывает одну фразу из ``source`` (экземпляр ``AudioSource``)... (сокращено)
     - **Параметры:**
       - `self`
       - `source`
       - `timeout` (по умолчанию: `None`)
       - `phrase_time_limit` (по умолчанию: `None`)
       - `snowboy_configuration` (по умолчанию: `None`)
       - `stream` (по умолчанию: `False`)
     - **Тип возвращаемого значения:** (`AudioData` или `generator`)
   ### `_listen(self, source, timeout=None, phrase_time_limit=None, snowboy_configuration=None, stream=False)`
     - **Докстринг:** Внутренний метод для прослушивания аудио.
     - **Параметры:** (Такие же, как у `listen`)
     - **Тип возвращаемого значения:** `generator`
   ### `listen_in_background(self, source, callback, phrase_time_limit=None)`
     - **Докстринг:** Запускает поток для многократной записи фраз из ``source``... (сокращено)
     - **Параметры:**
       - `self`
       - `source`
       - `callback`
       - `phrase_time_limit` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `function` (stopper)
   ### `recognize_sphinx(self, audio_data, language="en-US", keyword_entries=None, grammar=None, show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя CMU Sphinx... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`str` или `pocketsphinx.pocketsphinx.Decoder`)
   ### `recognize_google_cloud(self, audio_data, credentials_json=None, language="en-US", preferred_phrases=None, show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Google Cloud Speech API... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`str` или `dict`)
   ### `recognize_wit(self, audio_data, key, show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Wit.ai API... (сокращено)
     - **Параметры:**
       - `self`
       - `audio_data`
       - `key`
       - `show_all` (по умолчанию: `False`)
     - **Тип возвращаемого значения:** (`str` или `dict`)
   ### `recognize_azure(self, audio_data, key, language="en-US", profanity="masked", location="westus", show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Microsoft Azure Speech API... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`tuple[str, float]` или `dict`)
   ### `recognize_bing(self, audio_data, key, language="en-US", show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Microsoft Bing Speech API... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`str` или `dict`)
   ### `recognize_lex(self, audio_data, bot_name, bot_alias, user_id, content_type="audio/l16; rate=16000; channels=1", access_key_id=None, secret_access_key=None, region=None)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Amazon Lex API... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** `str`
   ### `recognize_houndify(self, audio_data, client_id, client_key, show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Houndify API... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`tuple[str, float]` или `dict`)
   ### `recognize_amazon(self, audio_data, bucket_name=None, access_key_id=None, secret_access_key=None, region=None, job_name=None, file_key=None)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Amazon Transcribe... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`tuple[str, float]` или `None`)
   ### `recognize_assemblyai(self, audio_data, api_token, job_name=None, **kwargs)`
     - **Докстринг:** Обертка для сервиса STT AssemblyAI. https://www.assemblyai.com/
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`tuple[str, float]` или `None`)
   ### `recognize_ibm(self, audio_data, key, language="en-US", show_all=False)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя IBM Speech to Text API... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`tuple[str, float or None]` или `dict`)
   ### `recognize_tensorflow(self, audio_data, tensor_graph='tensorflow-data/conv_actions_frozen.pb', tensor_label='tensorflow-data/conv_actions_labels.txt')`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя TensorFlow... (сокращено)
     - **Параметры:**
       - `self`
       - `audio_data`
       - `tensor_graph` (по умолчанию: `'tensorflow-data/conv_actions_frozen.pb'`)
       - `tensor_label` (по умолчанию: `'tensorflow-data/conv_actions_labels.txt'`)
     - **Тип возвращаемого значения:** (`str` или `None`)
   ### `recognize_whisper(self, audio_data, model="base", show_dict=False, load_options=None, language=None, translate=False, **transcribe_options)`
     - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Whisper... (сокращено)
     - **Параметры:** (Много, сокращено)
     - **Тип возвращаемого значения:** (`str` или `dict`)
   ### `recognize_vosk(self, audio_data, language='en')`
     - **Докстринг:** Распознает речь с помощью Vosk API.
     - **Параметры:**
       - `self`
       - `audio_data`
       - `language` (по умолчанию: `'en'`)
     - **Тип возвращаемого значения:** `str`

## `PortableNamedTemporaryFile(object)`
 - **Докстринг:** Ограниченная замена для ``tempfile.NamedTemporaryFile``...
 - **Методы:**
   ### `__init__(self, mode="w+b")`
     - **Параметры:**
       - `self`
       - `mode` (по умолчанию: `"w+b"`)
   ### `__enter__(self)`
     - **Тип возвращаемого значения:** `self`
   ### `__exit__(self, exc_type, exc_value, traceback)`
   ### `write(self, *args, **kwargs)`
   ### `writelines(self, *args, **kwargs)`
   ### `flush(self, *args, **kwargs)`

## Функции

### `recognize_api(self, audio_data, client_access_token, language="en", session_id=None, show_all=False)`
 - **Докстринг:** Распознает речь с помощью API.AI (теперь Dialogflow). Этот метод устарел.
 - **Параметры:** (Много, сокращено)
 - **Тип возвращаемого значения:** (`str` или `dict`)

# Файл: src/custom_speech_recognition/__main__.py
 - **Докстринг модуля:** `None`
 - **Примечание:** Этот файл является примером скрипта, демонстрирующим использование библиотеки `speech_recognition`. Он не содержит определений, предназначенных для использования в библиотеке.

# Файл: src/custom_speech_recognition/audio.py

## Классы

## `AudioData(object)`
 - **Докстринг:** Создает новый экземпляр ``AudioData``, представляющий монофонические аудиоданные...
 - **Методы:**
   ### `__init__(self, frame_data, sample_rate, sample_width)`
     - **Параметры:**
       - `self`
       - `frame_data`
       - `sample_rate`
       - `sample_width`
   ### `get_segment(self, start_ms=None, end_ms=None)`
     - **Докстринг:** Возвращает новый экземпляр ``AudioData``, обрезанный до заданного временного интервала...
     - **Параметры:**
       - `self`
       - `start_ms` (по умолчанию: `None`)
       - `end_ms` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `AudioData`
   ### `get_raw_data(self, convert_rate=None, convert_width=None)`
     - **Докстринг:** Возвращает байтовую строку, представляющую необработанные данные кадра для аудио...
     - **Параметры:**
       - `self`
       - `convert_rate` (по умолчанию: `None`)
       - `convert_width` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `bytes`
   ### `get_wav_data(self, convert_rate=None, convert_width=None)`
     - **Докстринг:** Возвращает байтовую строку, представляющую содержимое WAV-файла...
     - **Параметры:**
       - `self`
       - `convert_rate` (по умолчанию: `None`)
       - `convert_width` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `bytes`
   ### `get_aiff_data(self, convert_rate=None, convert_width=None)`
     - **Докстринг:** Возвращает байтовую строку, представляющую содержимое файла AIFF-C...
     - **Параметры:**
       - `self`
       - `convert_rate` (по умолчанию: `None`)
       - `convert_width` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `bytes`
   ### `get_flac_data(self, convert_rate=None, convert_width=None)`
     - **Докстринг:** Возвращает байтовую строку, представляющую содержимое файла FLAC...
     - **Параметры:**
       - `self`
       - `convert_rate` (по умолчанию: `None`)
       - `convert_width` (по умолчанию: `None`)
     - **Тип возвращаемого значения:** `bytes`

## Функции

### `get_flac_converter()`
 - **Докстринг:** Возвращает абсолютный путь к исполняемому файлу конвертера FLAC или вызывает `OSError`, если ни один не найден.
 - **Тип возвращаемого значения:** `str`

# Файл: resources/prompt/system_role/inbound_cs.py
 - **Докстринг модуля:** `None`
 - **Примечание:** Этот файл определяет многострочную строковую переменную `SYSTEM_ROLE`, используемую для конфигурации системы. Он не содержит определений, предназначенных для типичной библиотечной документации.
 - **Переменные:**
   - `SYSTEM_ROLE` (string)

# Файл: resources/prompt/system_role/phone_interview.py
 - **Докстринг модуля:** `None`
 - **Примечание:** Этот файл определяет многострочную строковую переменную `SYSTEM_ROLE`, используемую для конфигурации системы. Он не содержит определений, предназначенных для типичной библиотечной документации.
 - **Переменные:**
   - `SYSTEM_ROLE` (string)

# Файл: src/prompts.py

## Переменные

- `INITIAL_RESPONSE`

## Функции

### `create_prompt(transcript, lastContent, latest_response_text="")`
 - **Параметры:**
   - `transcript`
   - `lastContent`
   - `latest_response_text` (по умолчанию: `""`)
 - **Тип возвращаемого значения:** `str`

### `shutil_which(pgm)`
 - **Докстринг:** Совместимость с Python 2: бэкпорт ``shutil.which()`` из Python 3.
 - **Параметры:**
   - `pgm`
 - **Тип возвращаемого значения:** (`str` или `None`)

# Файл: src/custom_speech_recognition/exceptions.py

## Классы

### `SetupError(Exception)`

### `WaitTimeoutError(Exception)`

### `RequestError(Exception)`

### `UnknownValueError(Exception)`

### `TranscriptionNotReady(Exception)`

### `TranscriptionFailed(Exception)`

# Файл: src/custom_speech_recognition/recognizers/__init__.py
 - **Докстринг модуля:** `None`
 - **Примечание:** Этот файл пуст.

# Файл: src/custom_speech_recognition/recognizers/google.py

## Классы

## `RequestBuilder`
 - **Методы:**
   ### `__init__(self, *, endpoint: str, key: str, language: str, filter_level: ProfanityFilterLevel) -> None`
     - **Параметры:**
       - `self`
       - `endpoint: str`
       - `key: str`
       - `language: str`
       - `filter_level: ProfanityFilterLevel`
     - **Тип возвращаемого значения:** `None`
   ### `build(self, audio_data: AudioData) -> Request`
     - **Параметры:**
       - `self`
       - `audio_data: AudioData`
     - **Тип возвращаемого значения:** `Request`
   ### `build_url(self) -> str`
     - **Докстринг:** 
       ```
       >>> builder = RequestBuilder(endpoint="http://www.google.com/speech-api/v2/recognize", key="awesome-key", language="en-US", filter_level=0)
       >>> builder.build_url()
       'http://www.google.com/speech-api/v2/recognize?client=chromium&lang=en-US&key=awesome-key&pFilter=0'
       ```
     - **Параметры:**
       - `self`
     - **Тип возвращаемого значения:** `str`
   ### `build_headers(self, audio_data: AudioData) -> RequestHeaders`
     - **Докстринг:**
       ```
       >>> builder = RequestBuilder(endpoint="", key="", language="", filter_level=1)
       >>> audio_data = AudioData(b"", 16_000, 1)
       >>> builder.build_headers(audio_data)
       {'Content-Type': 'audio/x-flac; rate=16000'}
       ```
     - **Параметры:**
       - `self`
       - `audio_data: AudioData`
     - **Тип возвращаемого значения:** `RequestHeaders`
   ### `build_data(self, audio_data: AudioData) -> bytes`
     - **Параметры:**
       - `self`
       - `audio_data: AudioData`
     - **Тип возвращаемого значения:** `bytes`
   ### `to_convert_rate(sample_rate: int) -> int` (staticmethod)
     - **Докстринг:** Аудиосэмплы должны быть не менее 8 кГц
       ```
       >>> RequestBuilder.to_convert_rate(16_000)
       >>> RequestBuilder.to_convert_rate(8_000)
       >>> RequestBuilder.to_convert_rate(7_999)
       8000
       ```
     - **Параметры:**
       - `sample_rate: int`
     - **Тип возвращаемого значения:** `int`

## `OutputParser`
 - **Методы:**
   ### `__init__(self, *, show_all: bool, with_confidence: bool) -> None`
     - **Параметры:**
       - `self`
       - `show_all: bool`
       - `with_confidence: bool`
     - **Тип возвращаемого значения:** `None`
   ### `parse(self, response_text: str)`
     - **Параметры:**
       - `self`
       - `response_text: str`
     - **Тип возвращаемого значения:** (`dict` или `tuple` или `str`)
   ### `convert_to_result(response_text: str) -> Result` (staticmethod)
     - **Докстринг:** (Содержит doctests)
     - **Параметры:**
       - `response_text: str`
     - **Тип возвращаемого значения:** `Result`
   ### `find_best_hypothesis(alternatives: list[Alternative]) -> Alternative` (staticmethod)
     - **Докстринг:** (Содержит doctests)
     - **Параметры:**
       - `alternatives: list[Alternative]`
     - **Тип возвращаемого значения:** `Alternative`

## Функции

### `create_request_builder(*, endpoint: str, key: str | None = None, language: str = "en-US", filter_level: ProfanityFilterLevel = 0) -> RequestBuilder`
 - **Параметры:**
   - `endpoint: str`
   - `key: str | None` (по умолчанию: `None`)
   - `language: str` (по умолчанию: `"en-US"`)
   - `filter_level: ProfanityFilterLevel` (по умолчанию: `0`)
 - **Тип возвращаемого значения:** `RequestBuilder`

### `obtain_transcription(request: Request, timeout: int) -> str`
 - **Параметры:**
   - `request: Request`
   - `timeout: int`
 - **Тип возвращаемого значения:** `str`

### `recognize_legacy(recognizer, audio_data: AudioData, key: str | None = None, language: str = "en-US", pfilter: ProfanityFilterLevel = 0, show_all: bool = False, with_confidence: bool = False, *, endpoint: str = ENDPOINT)`
 - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя Google Speech Recognition API... (сокращено)
 - **Параметры:** (Много, сокращено)
 - **Тип возвращаемого значения:** (`str` или `dict` или `tuple`)

# Файл: src/custom_speech_recognition/recognizers/whisper.py

## Функции

### `recognize_whisper_api(recognizer, audio_data: "AudioData", *, model: str = "whisper-1", api_key: str | None = None)`
 - **Докстринг:** Выполняет распознавание речи для ``audio_data`` (экземпляр ``AudioData``), используя OpenAI Whisper API. Эта функция требует учетной записи OpenAI; посетите https://platform.openai.com/signup, затем сгенерируйте ключ API в `User settings <https://platform.openai.com/account/api-keys>`__. Подробнее: https://platform.openai.com/docs/guides/speech-to-text. Вызывает исключение ``speech_recognition.exceptions.SetupError``, если есть какие-либо проблемы с установкой openai или отсутствует переменная окружения.
 - **Параметры:**
   - `recognizer`
   - `audio_data: "AudioData"`
   - `model: str` (по умолчанию: `"whisper-1"`)
   - `api_key: str | None` (по умолчанию: `None`)
 - **Тип возвращаемого значения:** `str`
