##src/GPTResponder.py

import threading
import openai
from .prompts import create_prompt, INITIAL_RESPONSE
import time
import sys
from .config import SystemConfig,EnvConfig

class GPTResponder:
    def __init__(self, response_manager):
        self.response_manager = response_manager
        self.response = ""
        self._response_update_interval = 2
        self._lock = threading.Lock()
        self._processing = False
        self._last_processed_id = None
        # Инициализация конфигурации OpenAI
        if not self._initialize_openai():
            raise ValueError("Не удалось инициализировать конфигурацию OpenAI. Проверьте ваш API-ключ и настройки LLM.")

    def _initialize_openai(self) -> bool:
        """
        Инициализирует конфигурацию OpenAI или совместимого LLM.
        
        Returns:
            bool: True в случае успешной инициализации, иначе False.
        """
        llm_provider = EnvConfig.get_llm_provider()
        api_base_url = EnvConfig.get_llm_api_base_url()

        if api_base_url:
            openai.api_base = api_base_url
            print(f"Используется пользовательский базовый URL API: {api_base_url}")

        # Продолжить с настройкой API-ключа, если это OpenAI или OpenAI-совместимый API (указано через api_base_url)
        if llm_provider == "openai" or api_base_url:
            if not EnvConfig.ensure_api_key(): # Эта проверка теперь условная в EnvConfig
                print("Проверка API-ключа не удалась для OpenAI или пользовательского OpenAI-совместимого провайдера.")
                return False
            openai.api_key = EnvConfig.get_openai_key()
            print(f"Используется API-ключ OpenAI для провайдера: {llm_provider}")
        elif llm_provider != "openai":
            # Обработка других провайдеров при необходимости в будущем.
            # На данный момент, если это не 'openai' и api_base не установлен,
            # мы предполагаем, что это может быть конфигурация для другой, не OpenAI SDK интеграции.
            # Текущая структура, скорее всего, не сработает, если она не совместима с OpenAI.
            print(f"Провайдер LLM: '{llm_provider}'. API-ключ или базовый URL не настроены для прямого использования OpenAI SDK.")
            # В зависимости от будущих провайдеров, мы можем вернуть True или обработать иначе.
            # Пока что, если это не openai и нет base_url, это означает, что мы не можем напрямую использовать openai SDK.
            # Однако, ensure_api_key в EnvConfig уже учитывает провайдера.
            # Будем пока полагаться на логику ensure_api_key.
            if not EnvConfig.ensure_api_key():
                 print(f"Проверка API-ключа не удалась для провайдера: {llm_provider}")
                 return False
            # Если не-OpenAI провайдер все еще использует API-ключ, установленный через OPENAI_API_KEY, он будет загружен здесь.
            # Эта часть может потребовать доработки при активной поддержке других провайдеров.
            loaded_key = EnvConfig.get_openai_key()
            if loaded_key and loaded_key != 'your_api_key_here':
                openai.api_key = loaded_key # Это может быть приемлемо, если другой провайдер использует схожий механизм ключей
                print(f"Загружен API-ключ для провайдера: {llm_provider}. Поведение зависит от SDK/API провайдера.")
            else:
                print(f"Конкретный API-ключ не найден или не настроен для не-OpenAI провайдера '{llm_provider}' через OPENAI_API_KEY.")


        return True

    def _generate_response_from_transcript(self, lastContent, latest_response_text="", latest_response_q_text="", current_response_id=None):
        """
        Генерирует потоковый ответ из содержимого транскрипции.
        
        Args:
            lastContent (str): Последнее содержимое транскрипции.
            latest_response_text (str): Содержимое предыдущего ответа.
            latest_response_q_text (str): Содержимое предыдущего вопроса.
            current_response_id (str): ID текущего ответа.
            
        Yields:
            str: Сгенерированная часть содержимого ответа.
        """
        # Добавляем фильтрацию короткого содержимого
        if lastContent.strip() == "" or len(lastContent.strip()) < 4:
            print(f"Пропуск из-за слишком короткого содержимого (длина: {len(lastContent.strip())})")
            return

        conversation_history = []
        recent_speakers = [f"Speaker: [{latest_response_q_text}]\n\n"] # "Speaker" можно оставить, т.к. это часть формата промпта
        conversation_history.extend(recent_speakers)

        # Добавить отладочную информацию
        #print(f"\nОтладка generate_response_from_transcript:")
        #print(f"Последний ответ: {latest_response_text}")
        
        # Объединить записи в строку
        recent_transcript = "".join(conversation_history)
        #print(f"Недавняя транскрипция: {recent_transcript}")
        #print(f"Последнее содержимое: {lastContent}")
        
        try:
            content = create_prompt(recent_speakers, lastContent, latest_response_text)
            #print(f"Созданный промпт: {content}")

            # Получить имя модели из конфигурации
            model_name = EnvConfig.get_llm_model_name()
            print(f"Используется модель LLM: {model_name}")

            # Использовать потоковый API
            stream = openai.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SystemConfig.get_system_role()},
                    {"role": "user", "content": content},
                ],
                temperature=0.6,
                stream=True  # Включить потоковый ответ
            )

            accumulated_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    accumulated_response += chunk_content
                    
                    # Попытка разобрать содержимое в квадратных скобках
                    try:
                        if '[' in accumulated_response and ']' in accumulated_response:
                            response_text = accumulated_response.split("[")[1].split("]")[0]
                        else:
                            response_text = accumulated_response
                            
                        # Обновить ответ
                        if current_response_id:
                            self.response = response_text
                            self.response_manager.update_response(
                                current_response_id,
                                response_text,
                                is_complete=False
                            )
                        
                        yield response_text
                        
                    except Exception as e:
                        print(f"Ошибка разбора чанка: {e}")
                        yield chunk_content

            # По завершении пометить как полный ответ
            if current_response_id:
                try:
                    # Попытка получить содержимое в квадратных скобках, если не удается, использовать полный ответ
                    if '[' in accumulated_response and ']' in accumulated_response:
                        final_response = accumulated_response.split("[")[1].split("]")[0]
                    else:
                        print("В ответе не найдены квадратные скобки, используется полный ответ")
                        final_response = accumulated_response
                    
                    self.response_manager.update_response(
                        current_response_id,
                        final_response,
                        is_complete=True
                    )
                except Exception as e:
                    print(f"Ошибка обработки окончательного ответа: {e}")
                    # Если разбор не удался, использовать накопленный полный ответ
                    self.response_manager.update_response(
                        current_response_id,
                        accumulated_response,
                        is_complete=True
                    )
                
        except Exception as e:
            print(f"Ошибка в generate_response: {e}")
            error_message = str(e)
            if current_response_id:
                self.response_manager.update_response(
                    current_response_id,
                    error_message,
                    is_complete=True
                )
            yield error_message

    def respond_to_transcriber(self, transcriber):
        """
        Постоянно прослушивает и отвечает на вывод транскрибатора.
        
        Args:
            transcriber: Экземпляр транскрибатора.
        """
        while True:
            try:
                # Сначала ждем transcript_changed_event
                if transcriber.transcript_changed_event.wait(0.1):
                    transcriber.transcript_changed_event.clear()
                    
                    if transcriber.structured_transcript["speaker"]:
                        latest_record = transcriber.structured_transcript["speaker"][0]
                        current_response_id = latest_record[2]
                        
                        if (current_response_id and 
                            current_response_id != self._last_processed_id and 
                            not self._processing):
                            
                            with self._lock:
                                self._processing = True
                            
                            try:
                                question_text = latest_record[0]
                                self.response = "Думаю..." # Thinking...
                                self.response_manager.update_response(current_response_id, self.response)
                                
                                latest_response = self.response_manager.get_response(self._last_processed_id)
                                latest_response_text = ""
                                latest_response_q_text = ""
                                if latest_response and latest_response.is_complete:
                                    latest_response_text = latest_response.response_text
                                    latest_response_q_text = latest_response.question_text
                                
                                response_text = ''
                                # Использовать генератор для обработки потокового ответа
                                for response_text in self._generate_response_from_transcript(
                                    question_text,
                                    latest_response_text,
                                    latest_response_q_text,
                                    current_response_id
                                ):
                                    if response_text.strip():
                                        #print(f"Сгенерирован частичный ответ: {response_text}")
                                        self.response = response_text
                                
                                print(f"Сгенерированный ответ: {response_text}")
                                self._last_processed_id = current_response_id
                                
                            finally:
                                with self._lock:
                                    self._processing = False
            
            except Exception as e:
                print(f"Ошибка в respond_to_transcriber: {e}")
                time.sleep(0.1)

    def update_response_interval(self, interval):
        self._response_update_interval = interval