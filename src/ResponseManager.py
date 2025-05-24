# src/ResponseManager.py

import uuid
from dataclasses import dataclass
from typing import Optional, Dict, List
import threading
import json
import os
import traceback
from datetime import datetime, timezone
import pytz


@dataclass
class Response:
    """Класс данных для хранения информации об одном ответе."""
    response_id: str
    question_time: datetime
    question_text: str
    response_time: Optional[datetime] = None
    response_text: Optional[str] = None
    is_complete: bool = False # Флаг, указывающий, завершен ли ответ

    def to_dict(self):
        """Преобразует объект Response в словарь, пригодный для сериализации."""
        return {
            'response_id': self.response_id,
            'question_time': self.question_time.isoformat() if self.question_time else None,
            'question_text': self.question_text,
            'response_time': self.response_time.isoformat() if self.response_time else None,
            'response_text': self.response_text,
            'is_complete': self.is_complete
        }
    
class ResponseManager:
    """
    Класс для управления ответами. 
    Отвечает за создание, обновление, хранение и экспорт ответов.
    """
    def __init__(self):
        self._responses: Dict[str, Response] = {} # Словарь для хранения ответов
        self._lock = threading.Lock() # Блокировка для потокобезопасного доступа
        self._latest_response_id: Optional[str] = None # ID последнего ответа
        self._new_response_event = threading.Event() # Событие для сигнализации о новом ответе
        # Получение локальной временной зоны
        self._local_tz = datetime.now().astimezone().tzinfo

    def _convert_to_local_time(self, dt: datetime) -> datetime:
        """Преобразует время в локальную временную зону."""
        if dt.tzinfo is None:
            # Если у времени нет информации о временной зоне, предполагаем UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(self._local_tz)

    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Форматирует дату и время в строку локального времени."""
        if dt is None:
            return None
        local_dt = self._convert_to_local_time(dt)
        return local_dt.isoformat()

    def export_responses(self) -> list:
        """
        Экспортирует все данные ответов в формате, пригодном для сериализации.
        
        Returns:
            list: Список, содержащий все данные ответов.
        """
        with self._lock:
            try:
                # Сортировка ответов по времени в обратном хронологическом порядке (новые сначала)
                sorted_responses = sorted(
                    self._responses.values(),
                    key=lambda x: x.question_time,
                    reverse=True  # Новые впереди
                )
                
                # Преобразование в формат, пригодный для сериализации
                responses_data = [response.to_dict() for response in sorted_responses]
                
                print(f"Экспортируется {len(responses_data)} ответов")  # Отладочная информация
                return responses_data
                
            except Exception as e:
                print(f"Ошибка при экспорте ответов: {e}")
                return []

    def save_responses_to_file(self, filepath: str) -> bool:
        """
        Сохраняет данные ответов в JSON-файл.
        
        Args:
            filepath (str): Путь для сохранения файла.
            
        Returns:
            bool: True в случае успешного сохранения, иначе False.
        """
        try:
            # Получение данных
            data = self.export_responses()
            
            if not data:
                print("Нет ответов для экспорта")
                return False
                
            print(f"Сохранение {len(data)} ответов в {filepath}")  # Отладочная информация
            
            # Убедиться, что файл имеет расширение .json
            if not filepath.endswith('.json'):
                filepath += '.json'
            
            # Сохранение файла
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Проверка, что файл успешно сохранен
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                print(f"Успешно сохранено в {filepath}")
                return True
            else:
                print(f"Файл был создан, но может быть пустым: {filepath}")
                return False
                
        except Exception as e:
            print(f"Ошибка при сохранении ответов: {e}")
            import traceback
            traceback.print_exc()  # Печать подробной информации об ошибке
            return False

    def export_structured_conversation(self, structured_transcript: dict, reverse_chronological: bool = False) -> dict:
        """
        Экспортирует полные данные диалога на основе structured_transcript, используя локальную временную зону.
        """
        with self._lock:
            try:
                # Получение объединенных сообщений
                combined_messages = list(structured_transcript.get("combined", []))
                
                # Извлечение сообщений типа "speaker"
                speaker_messages = []
                other_messages = []
                #print (f'Объединенные: {combined_messages}') # Отладка
                #print (f'---------------') # Отладка
                # Разделение сообщений "speaker" и других типов
                for msg in combined_messages:
                    text, timestamp, response_id, speaker_type = msg
                    if speaker_type == "speaker":
                        speaker_messages.append(msg)
                    else:
                        other_messages.append(msg)
                
                new_speaker_messages = [] # Инициализация здесь
                # Если есть сообщения от "speaker", выполнить обработку сдвига response_id
                if speaker_messages:
                    # Получение всех response_id
                    response_ids = [msg[2] for msg in speaker_messages]  # [id1, id2, id3, ...]
                    
                    # Сдвиг response_id (первый становится None, остальные сдвигаются)
                    shifted_response_ids = [None] + response_ids[:-1] # [None, id1, id2, ...] - исправлено, чтобы последний ID не дублировался
                    
                    # Обновление response_id в speaker_messages
                    for i, msg in enumerate(speaker_messages):
                        text, timestamp, _, speaker_type = msg # Старый response_id игнорируется
                        new_response_id = shifted_response_ids[i]
                        new_speaker_messages.append((text, timestamp, new_response_id, speaker_type))
                else: # Если нет сообщений от спикера, new_speaker_messages остается пустым
                    pass

                # Объединение сообщений по временной метке
                all_messages = []
                all_messages.extend(new_speaker_messages)
                all_messages.extend(other_messages)
                # Сортировка по временной метке
                all_messages.sort(key=lambda x: x[1])
                
                # Установка порядка сортировки
                # Если нужен обратный хронологический порядок (от новых к старым), инвертировать список
                if reverse_chronological:
                    all_messages.reverse()                

                # Создание словаря ответов для быстрого доступа
                responses_dict = {}
                for response_id_key, response_obj in self._responses.items(): # Используем разные имена переменных
                    if response_id_key: # Убедимся, что response_id_key не None
                        responses_dict[response_id_key] = {
                            "id": response_id_key,
                            "question_time": self._format_datetime(response_obj.question_time),
                            "question_text": response_obj.question_text,
                            "response_time": self._format_datetime(response_obj.response_time),
                            "response_text": response_obj.response_text,
                            "is_complete": response_obj.is_complete
                        }
                
                # Создание структуры данных для экспорта
                export_data = {
                    "metadata": {
                        "export_time": self._format_datetime(datetime.now().astimezone(self._local_tz)),
                        "version": "2.0", # Версия формата экспорта
                        "total_messages": len(all_messages), # Общее количество сообщений
                        "order": "newest_first" if reverse_chronological else "oldest_first", # Порядок сортировки
                        "timezone": str(self._local_tz) # Временная зона
                    },
                    "conversation": {
                        "messages": []
                    }
                }
                
                # Формирование окончательного списка сообщений
                for idx, (text, timestamp, current_response_id, speaker_type) in enumerate(all_messages): # Используем current_response_id
                    message = {
                        "role": speaker_type,
                        "text": text,
                        "timestamp": self._format_datetime(timestamp),
                        "response_id": current_response_id,
                        "index": idx
                    }
                    
                    # Добавление ответа только для действительных response_id
                    if current_response_id and current_response_id in responses_dict:
                        message["response"] = responses_dict[current_response_id]
                    
                    export_data["conversation"]["messages"].append(message)
                
                # Отладочный вывод
                if hasattr(self, 'debug_mode') and self.debug_mode:
                    print("\nОтладка - Обработка сообщений:")
                    print("\nИсходные сообщения спикера:")
                    for msg in speaker_messages: # Используем оригинальные speaker_messages для отладки до сдвига
                        print(f"Текст: {msg[0]}, ID ответа: {msg[2]}")
                        
                    print("\nОбработанные сообщения (в экспорте):")
                    for msg in export_data["conversation"]["messages"]:
                        if msg["role"] == "speaker":
                            print(f"Текст: {msg['text']}")
                            print(f"ID ответа: {msg['response_id']}")
                            if "response" in msg:
                                print(f"Текст ответа: {msg['response']['response_text']}")
                            print("---")
                
                return export_data
                
            except Exception as e:
                print(f"Ошибка при экспорте структурированного диалога: {e}")
                traceback.print_exc()
                return {}
                    
    def save_structured_conversation(self, filepath: str, structured_transcript: dict) -> bool:
        """
        Сохраняет структурированные данные диалога в JSON-файл.
        
        Args:
            filepath: Путь для сохранения файла.
            structured_transcript: Структурированные записи диалога.
                
        Returns:
            bool: True в случае успешного сохранения, иначе False.
        """
        try:
            # Получение структурированных данных диалога
            data = structured_transcript # structured_transcript уже является данными для сохранения
            
            if not data or not data.get("conversation", {}).get("messages"): # Проверка наличия сообщений
                print("Нет данных диалога для экспорта")
                return False
                
            print(f"Сохранение диалога с {len(data['conversation']['messages'])} сообщениями")
            
            # Убедиться, что расширение файла правильное
            if not filepath.endswith('.json'):
                filepath += '.json'
            
            # Сохранение файла
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Проверка успешности сохранения файла
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                print(f"Диалог успешно сохранен в {filepath}")
                return True
            else:
                print(f"Файл был создан, но может быть пустым: {filepath}")
                return False
                
        except Exception as e:
            print(f"Ошибка при сохранении диалога: {e}")
            traceback.print_exc()
            return False

    def create_response(self, question_time: datetime, question_text: str) -> str:
        """Создает запись ответа для нового вопроса, возвращает response_id."""
        response_id = str(uuid.uuid4())
        with self._lock:
            # Обработка времени ввода
            if question_time.tzinfo is None: # Если нет информации о временной зоне
                question_time = question_time.replace(tzinfo=timezone.utc) # Считаем UTC
            question_time = question_time.astimezone(self._local_tz) # Конвертируем в локальное время   

            self._responses[response_id] = Response(
                response_id=response_id,
                question_time=question_time,
                question_text=question_text
            )
            self._latest_response_id = response_id
        return response_id

    def update_response(self, response_id: str, response_text: str, 
                    is_complete: bool = False, is_incremental: bool = False):
        """Обновляет содержимое ответа, поддерживает инкрементное обновление."""
        with self._lock:
            if response_id not in self._responses:
                #print(f"Попытка обновить несуществующий response_id: {response_id}") # Отладка
                return False # Ответ не найден
            
            response = self._responses[response_id]
            if response.response_time is None: # Установить время ответа, если его еще нет
                response.response_time = datetime.now().astimezone(self._local_tz)
            
            if is_incremental: # Инкрементное добавление текста
                response.response_text = (response.response_text or "") + response_text
            else: # Полная замена текста
                response.response_text = response_text
                
            response.is_complete = is_complete # Обновление статуса завершенности
            
            if is_complete: # Если ответ завершен, сигнализировать событию
                self._new_response_event.set()
            return True
            
    def get_response(self, response_id: str) -> Optional[Response]:
        """Получает указанный ответ по его ID."""
        #print(f"Получение Response ID: {response_id}")
        return self._responses.get(response_id)
    
    def get_latest_response(self) -> Optional[Response]:
        """Получает самый последний ответ."""
        #print(f"Получение последнего ответа:\n\n") # Отладка
        #print(f"ID последнего ответа: {self._latest_response_id} \n\n") # Отладка

        if self._latest_response_id:
            return self._responses.get(self._latest_response_id)
        return None # Если нет последнего ID, вернуть None
    
    def wait_for_new_response(self, timeout: Optional[float] = None) -> bool:
        """Ожидает нового полного ответа."""
        result = self._new_response_event.wait(timeout) # Ожидание события
        if result: # Если событие сработало
            self._new_response_event.clear() # Сброс события
        return result