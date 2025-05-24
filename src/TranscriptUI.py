# src/TranscriptUI.py

import customtkinter as ctk
from typing import Optional, Dict, List, Any
import traceback

class TranscriptUI:
    """Обрабатывает отображение и взаимодействие с UI записей диалога."""
    
    def __init__(self, textbox: ctk.CTkTextbox, response_manager: Any):
        """
        Инициализирует TranscriptUI.
            
        Args:
            textbox: CTkTextbox для отображения записей диалога.
            response_manager: Экземпляр ResponseManager для управления ответами на диалоги.
        """
        self.textbox = textbox
        self.text_widget = textbox._textbox # Доступ к внутреннему текстовому виджету Tkinter
        self.response_manager = response_manager
        self.last_speaker_count = 0 # Счетчик последних записей говорящего
        self.last_you_count = 0 # Счетчик последних ваших записей
        self.debug_mode = False # Режим отладки
        self.is_response_locked = False # Заблокирован ли ответ (для предотвращения автообновления)
        self.response_textbox = None # Текстовое поле для отображения ответа
        self.selected_response_id = None # ID выбранного ответа
        self.last_response_id = None # ID последнего полученного ответа
        self.current_streaming_id = None  # ID текущего потокового обновления
        self.latest_speaker_response = None  # Отслеживание последнего ответа Говорящего
        self.last_speaker_content = {}  # Словарь для отслеживания последнего содержимого каждой записи Говорящего
        self.last_you_content = {} # Словарь для отслеживания последнего содержимого каждой вашей записи
        self._initialize_default_lines() # Инициализация строк по умолчанию

        # Конфигурация текстового поля
        self._configure_textbox()
        
        # Регистрация обратного вызова обновления ответа
        if hasattr(response_manager, 'register_update_callback'):
            response_manager.register_update_callback(self._on_response_update)
        
        if self.debug_mode:
            print("TranscriptUI инициализирован")

    def _initialize_default_lines(self) -> None:
        """Инициализирует строки по умолчанию для Говорящего и Вас."""
        try:
            self.text_widget.configure(state="normal") # Включить редактирование
            
            # Вставка строки Говорящего
            speaker_text = "Говорящий: [Готов...]\n\n" # Speaker: [Ready...]
            self.text_widget.insert("1.0", speaker_text)
            
            # Вставка строки Вы
            you_text = "Вы: [Готов...]\n\n" # You: [Ready...]
            self.text_widget.insert("1.0", you_text)
            
            # Добавление тега для строк по умолчанию
            self.text_widget.tag_add("default_line", "1.0", "3.0") # Применить тег к первым двум строкам
            self.text_widget.tag_configure("default_line", foreground='#666666') # Цвет для строк по умолчанию
            
            self.text_widget.configure(state="normal") # Оставить редактируемым (или "disabled", если не нужно начальное редактирование)
            
        except Exception as e:
            print(f"Ошибка инициализации строк по умолчанию: {e}")
            traceback.print_exc()

    def _configure_textbox(self) -> None:
        """Конфигурирует основные настройки текстового поля."""
        self.textbox.configure(cursor="hand2") # Курсор в виде руки при наведении
        self.text_widget.configure(state="normal")  # Убедиться, что текст можно выбирать
        
    def toggle_debug(self, enabled: bool = None) -> None:
        """
        Переключает режим отладки.
        
        Args:
            enabled: Если предоставлено, напрямую устанавливает состояние режима отладки;
                     если не предоставлено, переключает текущее состояние.
        """
        if enabled is None:
            self.debug_mode = not self.debug_mode
        else:
            self.debug_mode = enabled
        print(f"Режим отладки {'включен' if self.debug_mode else 'выключен'}.")
       
    def update_transcript(self, transcriber: Any) -> None:
        """
        Обновляет отображение записей диалога (потоковое обновление).
        
        Args:
            transcriber: Экземпляр AudioTranscriber, содержащий данные записей диалога.
        """
        try:
            current_speaker_count = len(transcriber.structured_transcript['speaker'])
            current_you_count = len(transcriber.structured_transcript['you'])
            
            # Вывод отладочной информации только при изменениях
            if (current_speaker_count != self.last_speaker_count or 
                current_you_count != self.last_you_count):
                if self.debug_mode:
                    print("\nОтладка обновления TranscriptUI:")
                    print(f"Текущее количество записей говорящего: {current_speaker_count}")
                    print(f"Текущее количество ваших записей: {current_you_count}")
                    print(f"Последнее количество записей говорящего: {self.last_speaker_count}")
                    print(f"Последнее количество ваших записей: {self.last_you_count}")
            
            # Получение новых записей
            new_records = self._get_new_records(transcriber)
            
            if new_records and self.debug_mode:
                print(f"Найдены новые записи: {len(new_records)}")
                print("Содержимое новых записей:")
                for record in new_records:
                    print(f"- {record['type']}: {record['text']}")
            
            # Если есть новые записи, добавить их к отображению
            if new_records:
                # Сохранение текущего состояния выделения и позиции прокрутки
                try:
                    selection_start = self.text_widget.index("sel.first")
                    selection_end = self.text_widget.index("sel.last")
                    has_selection = True
                except: # tk.TclError если нет выделения
                    has_selection = False
                
                current_pos = self.textbox.yview()[1]  # Использование нижней позиции
                was_at_bottom = current_pos >= 0.9  # Считаем, что внизу, если близко к низу
                
                # Временно включить текстовое поле для обновления содержимого
                self.text_widget.configure(state="normal")
                
                # Добавление новых записей
                for record in new_records:
                    record_type_translated = "Говорящий" if record["type"] == "Speaker" else "Вы"
                    # Поиск первой соответствующей записи
                    line_start = self.text_widget.search(
                        f"{record_type_translated}:", # Используем переведенный тип
                        "1.0", 
                        stopindex="end"
                    )
                    
                    if line_start:
                        # Найти начало следующей записи или конец текста
                        next_record_start = self.text_widget.search(
                            f"(Говорящий:|Вы:)", # Используем переведенные типы
                            f"{line_start} + 1c", 
                            stopindex="end",
                            regexp=True # Включить регулярные выражения для поиска одного из двух
                        )
                        # Определение диапазона удаления
                        delete_end = next_record_start if next_record_start else "end"

                    if record["is_update"]:
                        # Обновление содержимого последней записи
                            existing_tags = self.text_widget.tag_names(line_start)
                            response_id = None
                            for tag in existing_tags:
                                if tag.startswith("response_"):
                                    response_id = tag.replace("response_", "")
                                    break                            
                            # Удаление всего содержимого текущей записи (включая пустые строки)
                            self.text_widget.delete(line_start, delete_end)
                            
                            # Вставка обновленного содержимого
                            text = f"{record_type_translated}: [{record['text']}]\n\n"
                            self.text_widget.insert(line_start, text)
                            if response_id:
                                record['response_id'] = response_id # Убедиться, что ID ответа сохраняется
                                self._add_record_tags(line_start, record) # Переприменить теги
                    else:
                        # Удаление всего содержимого текущей записи (включая пустые строки)
                        self.text_widget.delete(line_start, delete_end)
                        # Расчет позиции вставки (всегда в начало для новых)
                        insert_position = "1.0"
                        text = f"{record_type_translated}: [{record['text']}]\n\n"
                        self.text_widget.insert(insert_position, text)
                        
                        # Если у записи есть response_id, добавить тег и интерактивность
                        if record['response_id']:
                            self._add_record_tags(insert_position, record)
                            # Если это запись Говорящего, обновить последний ответ
                            if record['type'] == 'Speaker': # Используем оригинальный тип для логики
                                self.latest_speaker_response = record['response_id']
                                response = self.response_manager.get_response(record['response_id'])
                                if response and response.response_text and not self.is_response_locked:
                                    self._update_response_text(response.response_text,response.question_text)
                        # Повторная вставка для "печатающегося" эффекта или индикатора ожидания
                        insert_position = "1.0"
                        text = f"{record_type_translated}: [Перехват...]\n\n" # Catching...
                        self.text_widget.insert(insert_position, text)                                                   
                self.text_widget.see("1.0") # Прокрутка к началу, чтобы видеть последние обновления

                # Восстановление состояния выделения
                if has_selection:
                    try:
                        self.text_widget.tag_add("sel", selection_start, selection_end)
                    except: # tk.TclError если старые индексы некорректны
                        pass

                # После обновления установить состояние для взаимодействия
                self.text_widget.configure(state="normal") # Или "disabled", если только для чтения
        
        except Exception as e:
            print(f"Ошибка в update_transcript: {str(e)}")
            traceback.print_exc()
            
        finally:
            # Установить следующее обновление, проверять наличие нового содержимого каждые 300 мс
            self.textbox.after(300, self.update_transcript, transcriber)

    def _get_new_records(self, transcriber: Any) -> List[Dict]:
        """
        Получает новые записи диалога, включая новые и обновленные существующие записи.
        
        Args:
            transcriber: Экземпляр AudioTranscriber.
            
        Returns:
            List[Dict]: Список новых и обновленных записей.
        """
        new_records = []
        
        try:
            current_speaker_records = transcriber.structured_transcript["speaker"]
            current_you_records = transcriber.structured_transcript["you"]
            
            # Обработка записей говорящего
            if current_speaker_records:
                # Проверка наличия новых записей
                if len(current_speaker_records) > self.last_speaker_count:
                    # При наличии новых записей обработать их
                    new_count = len(current_speaker_records) - self.last_speaker_count
                    for record in reversed(current_speaker_records[:new_count]): # Обрабатываем в обратном порядке, чтобы новые были первыми
                        text, timestamp, response_id = record
                        new_records.append({
                            "type": "Speaker", # Используем оригинальный тип для внутренней логики
                            "text": text,
                            "timestamp": timestamp,
                            "response_id": response_id,
                            "is_update": False
                        })
                        self.current_speaker_text = text # Обновляем текущий текст говорящего
                    self.last_speaker_count = len(current_speaker_records)
                else:
                    # При отсутствии новых записей проверить, не обновилась ли последняя
                    latest_record = current_speaker_records[0]
                    text, timestamp, response_id = latest_record
                    # Используем self.current_speaker_text для сравнения
                    if hasattr(self, 'current_speaker_text') and text != self.current_speaker_text:
                        new_records.append({
                            "type": "Speaker",
                            "text": text,
                            "timestamp": timestamp,
                            "response_id": response_id,
                            "is_update": True
                        })
                        self.current_speaker_text = text
            
            # Обработка ваших записей (аналогичная логика)
            if current_you_records:
                if len(current_you_records) > self.last_you_count:
                    new_count = len(current_you_records) - self.last_you_count
                    for record in reversed(current_you_records[:new_count]):
                        text, timestamp, response_id = record
                        new_records.append({
                            "type": "You", # Используем оригинальный тип для внутренней логики
                            "text": text,
                            "timestamp": timestamp,
                            "response_id": response_id,
                            "is_update": False
                        })
                        self.current_you_text = text
                    self.last_you_count = len(current_you_records)
                else:
                    latest_record = current_you_records[0]
                    text, timestamp, response_id = latest_record
                    if hasattr(self, 'current_you_text') and text != self.current_you_text:
                        new_records.append({
                            "type": "You",
                            "text": text,
                            "timestamp": timestamp,
                            "response_id": response_id,
                            "is_update": True
                        })
                        self.current_you_text = text
            
        except Exception as e:
            print(f"Ошибка в _get_new_records: {str(e)}")
            traceback.print_exc()
            
        # Сортировка по временной метке, новые впереди
        new_records.sort(key=lambda x: x["timestamp"], reverse=True)
        return new_records
      
    def _append_new_records(self, records: List[Dict]) -> None:
        """Добавляет новые записи в текстовое поле."""
        # Этот метод, похоже, не используется в текущей логике update_transcript,
        # так как update_transcript сам обрабатывает вставку/обновление.
        # Если он нужен, его также нужно будет локализовать.
        try:
            self.text_widget.configure(state="normal")
            insert_position = "1.0" # Новые записи всегда вставляются в начало
            
            latest_speaker_record = None
            
            for record in records:
                record_type_translated = "Говорящий" if record["type"] == "Speaker" else "Вы"
                text = f"{record_type_translated}: [{record['text']}]\n\n"
                self.text_widget.insert(insert_position, text)
                
                if record['response_id']:
                    self._add_record_tags(insert_position, record)
                    # Отслеживание последней записи Говорящего
                    if record['type'] == 'Speaker':
                        latest_speaker_record = record
            
            # После добавления всех записей обновить последний ответ
            if latest_speaker_record and not self.is_response_locked:
                self.latest_speaker_response = latest_speaker_record['response_id']
                response = self.response_manager.get_response(latest_speaker_record['response_id'])
                if response and response.response_text:
                    self.update_latest_response(latest_speaker_record['response_id'], response.response_text, response.question_text) # Добавлен question_text
                    
            self.text_widget.configure(state="normal") # Или "disabled"
            
        except Exception as e:
            print(f"Ошибка в _append_new_records: {e}")
            traceback.print_exc()

    def _add_record_tags(self, position: str, record: Dict) -> None:
        """
        Добавляет тег и интерактивность к записи.
        """
        try:
            # Точный расчет конца строки
            line_end = self.text_widget.index(f"{position} lineend")
            tag_name = f"response_{record['response_id']}"
            
            # Убедиться, что тег покрывает весь текст строки, включая символ новой строки
            self.text_widget.tag_add(tag_name, position, f"{line_end}+1c")
            
            # Остальные настройки тегов и интерактивности остаются без изменений
            # Hover background color depends on speaker type
            hover_bg = '#2f3746' if record['type'] == 'Speaker' else '#1f2736' # Темно-серый для Говорящего, чуть светлее для Вас
            self.text_widget.tag_configure(tag_name, background='') # Изначально без фона
            
            def on_enter(e, tag=tag_name, bg=hover_bg):
                try:
                    self.text_widget.tag_configure(tag, background=bg)
                except Exception as ex_on_enter: # Используем другое имя для исключения
                    print(f"Ошибка в on_enter: {ex_on_enter}")
                    
            def on_leave(e, tag=tag_name):
                try:
                    self.text_widget.tag_configure(tag, background='')
                except Exception as ex_on_leave: # Используем другое имя для исключения
                    print(f"Ошибка в on_leave: {ex_on_leave}")
            
            self.text_widget.tag_bind(tag_name, '<Enter>', on_enter)
            self.text_widget.tag_bind(tag_name, '<Leave>', on_leave)
            
            # Цвет текста для записей "Вы"
            if record['type'] == 'You':
                self.text_widget.tag_configure(tag_name, foreground='#A0A0A0') # Светло-серый
                
        except Exception as e:
            print(f"Ошибка в _add_record_tags: {str(e)}")
            traceback.print_exc()

    def _add_record_tags_(self, position: str, record: Dict) -> None:
        """
        Добавляет тег и интерактивность к записи. (Дублирующий метод, возможно, для отладки)
        
        Args:
            position: Позиция вставки.
            record: Данные записи.
        """
        try:
            # Получение конечной позиции вставленной строки текста
            line_end = self.text_widget.index(f"{position} lineend")
            tag_name = f"response_{record['response_id']}"
            
            # Добавление тега ко всей строке текста
            self.text_widget.tag_add(tag_name, position, f"{line_end}+1c")
            
            # Настройка стиля тега
            hover_bg = '#2f3746' if record['type'] == 'Speaker' else '#1f2736'
            self.text_widget.tag_configure(tag_name, background='')
            
            # Добавление эффекта при наведении мыши
            def on_enter(e, tag=tag_name, bg=hover_bg):
                try:
                    self.text_widget.tag_configure(tag, background=bg)
                except Exception as ex_on_enter:
                    print(f"Ошибка в on_enter: {ex_on_enter}")
                    
            def on_leave(e, tag=tag_name):
                try:
                    self.text_widget.tag_configure(tag, background='')
                except Exception as ex_on_leave:
                    print(f"Ошибка в on_leave: {ex_on_leave}")
            
            # Привязка событий мыши
            self.text_widget.tag_bind(tag_name, '<Enter>', on_enter)
            self.text_widget.tag_bind(tag_name, '<Leave>', on_leave)
            
            # Установка специального цвета для типа "You"
            if record['type'] == 'You':
                self.text_widget.tag_configure(tag_name, foreground='#A0A0A0')
            
            if self.debug_mode:
                print(f"Добавлен тег {tag_name} к тексту в позиции {position}")
                
        except Exception as e:
            print(f"Ошибка в _add_record_tags_ (дубликат): {str(e)}") # Указываем, что это дубликат
            traceback.print_exc()

    def _update_response_text_(self, response_text: str) -> None:
        """Обновляет содержимое текстового поля ответа. (Дублирующий метод)"""
        try:
            if not self.response_textbox:
                print("Предупреждение: response_textbox не инициализирован.")
                return

            current_text = self.response_textbox.get("1.0", "end-1c")
            if response_text != current_text:  # Обновлять только если содержимое изменилось
                self.response_textbox.configure(state="normal")
                self.response_textbox.delete("1.0", "end")
                self.response_textbox.insert("1.0", response_text)
                self.response_textbox.configure(state="normal") # Или "disabled"
        except Exception as e:
            print(f"Ошибка обновления текста ответа (дубликат): {e}")
            traceback.print_exc()

    def _update_response_text(self, response_text: str, question_text: str = None) -> None:
        """
        Обновляет содержимое текстового поля ответа, включая вопрос и ответ.
        
        Args:
            response_text: Текст ответа.
            question_text: Связанный текст вопроса.
        """
        try:
            if not self.response_textbox:
                print("Предупреждение: response_textbox не инициализирован.")
                return

            # Форматирование отображаемого содержимого
            display_text = self._format_response_display(question_text, response_text)
            #print (f'Отображаемый текст: {display_text}') # Отладка
            current_text = self.response_textbox.get("1.0", "end-1c")
            if display_text != current_text:  # Обновлять только если содержимое изменилось
                self.response_textbox.configure(state="normal")
                self.response_textbox.delete("1.0", "end")
                self.response_textbox.insert("1.0", display_text)
                self.response_textbox.configure(state="normal") # Или "disabled"
        except Exception as e:
            print(f"Ошибка обновления текста ответа: {e}")
            traceback.print_exc()

    def _format_response_display(self, question_text: Optional[str], response_text: str) -> str:
        """
        Форматирует отображение вопроса и ответа.
        
        Args:
            question_text: Текст вопроса.
            response_text: Текст ответа.
            
        Returns:
            str: Отформатированный текст для отображения.
        """
        if question_text:
            return f"В: {question_text}\n\n---\n\nО: {response_text}" # Q: -> В: (Вопрос), A: -> О: (Ответ)
        return response_text
    
    def clear(self) -> None:
        """Очищает все содержимое и счетчики."""
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.delete("1.0", "end")
            self.text_widget.configure(state="normal")  # Оставить выбираемым
            self.last_speaker_count = 0
            self.last_you_count = 0
            self._initialize_default_lines() # Переинициализировать строки по умолчанию
            if self.debug_mode:
                print("TranscriptUI очищен")
                
        except Exception as e:
            print(f"Ошибка в clear: {str(e)}")
            traceback.print_exc()

    def _on_response_update(self, response_id: str, response_text: str, is_complete: bool) -> None:
        """
        Обратный вызов для обновления ответа.
        
        Args:
            response_id: ID ответа.
            response_text: Обновленный текст ответа.
            is_complete: Завершен ли ответ.
        """
        try:
            # Принудительно обновить последний ответ, даже если он заблокирован,
            # если ID совпадает с выбранным или если ничего не выбрано.
            if self.is_response_locked and response_id != self.selected_response_id:
                return # Не обновлять, если заблокировано и ID не совпадает

            if not self.response_textbox:
                print("Предупреждение: response_textbox не инициализирован.")
                return
            # Получение связанного объекта ответа для получения текста вопроса
            response = self.response_manager.get_response(response_id)
            question_text = response.question_text if response else None
            self.response_textbox.configure(state="normal") # Включить для редактирования
            
            if not is_complete:
                # Если ответ еще не завершен, добавлять обновленный текст вместо замены всего содержимого (для потока)
                # Это может потребовать более сложной логики для правильного "потокового" отображения.
                # Пока что просто заменяем, как и для завершенного.
                display_text = self._format_response_display(question_text, response_text)
                self.response_textbox.delete("1.0", "end")
                self.response_textbox.insert("1.0", display_text)
            else:
                # Если ответ завершен, заменить все содержимое
                display_text = self._format_response_display(question_text, response_text)
                self.response_textbox.delete("1.0", "end")
                self.response_textbox.insert("1.0", display_text)
            
            self.response_textbox.configure(state="normal")  # Оставить выбираемым/редактируемым

            # Обновление ID последнего ответа
            self.last_response_id = response_id
            
            if self.debug_mode:
                print(f"Ответ обновлен: {response_id}, завершен: {is_complete}")
        except Exception as e:
            print(f"Ошибка в _on_response_update: {e}")
            traceback.print_exc()


    def update_latest_response(self, response_id: str, response_text: str, question_text: str = None) -> None:
        """Принудительно обновляет текст последнего ответа, независимо от состояния блокировки."""
        try:
            if not self.response_textbox:
                print("Предупреждение: response_textbox не инициализирован.")
                return
            display_text = self._format_response_display(question_text, response_text)
            self.response_textbox.configure(state="normal")
            self.response_textbox.delete("1.0", "end")
            self.response_textbox.insert("1.0", display_text)
            self.response_textbox.configure(state="normal")  # Оставить выбираемым

            if self.debug_mode:
                print(f"Последний ответ принудительно обновлен: {response_id}")
        except Exception as e:
            print(f"Ошибка в update_latest_response: {e}")
            traceback.print_exc()

    def add_click_handler(self, response_textbox: ctk.CTkTextbox) -> None:
        """Добавляет обработчик событий клика."""
        self.response_textbox = response_textbox

        def on_click(event):
            try:
                tags = self.text_widget.tag_names(f"@{event.x},{event.y}")
                for tag in tags:
                    if tag.startswith("response_"):
                        response_id = tag.replace("response_", "")
                        response = self.response_manager.get_response(response_id)
                        if response and response.response_text:
                            if self.selected_response_id == response_id:
                                # Разблокировать и восстановить автообновление
                                self.is_response_locked = False
                                self.selected_response_id = None
                                # Немедленно обновить до последнего ответа
                                if self.last_response_id:
                                    latest_response = self.response_manager.get_response(self.last_response_id)
                                    if latest_response and latest_response.response_text:
                                        self.update_latest_response(self.last_response_id, latest_response.response_text,latest_response.question_text)
                            else:
                                # Заблокировать и отобразить выбранный ответ
                                self.is_response_locked = True
                                self.selected_response_id = response_id
                                display_text = self._format_response_display(response.question_text, response.response_text)
                                self.response_textbox.configure(state="normal")
                                self.response_textbox.delete("1.0", "end")
                                self.response_textbox.insert("1.0", display_text)
                                self.response_textbox.configure(state="normal")
                            break
            except Exception as e:
                print(f"Ошибка в обработчике клика: {e}")
                traceback.print_exc()

        self.text_widget.bind('<Button-1>', on_click) # Привязка к левой кнопке мыши
        
        def unlock_response(event):
            # Проверка, был ли клик вне текстовых полей транскрипции или ответа
            if (str(event.widget) != str(self.text_widget) and 
                str(event.widget) != str(self.response_textbox._textbox)): # Сравнение внутренних виджетов
                self.is_response_locked = False
                self.selected_response_id = None
                
                # Восстановление отображения последнего ответа
                if self.last_response_id:
                    response = self.response_manager.get_response(self.last_response_id)
                    if response and response.response_text:
                        self.update_latest_response(self.last_response_id, response.response_text, response.question_text )

        root = self.textbox.winfo_toplevel() # Получение корневого окна
        root.bind('<Button-1>', unlock_response, add="+") # Добавление обработчика к корневому окну

    def is_response_frozen(self) -> bool:
        """
        Проверяет, заблокирован ли ответ.
        
        Returns:
            bool: True, если ответ заблокирован, иначе False.
        """
        return self.is_response_locked