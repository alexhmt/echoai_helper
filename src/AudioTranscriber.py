# src/AudioTranscriber.py

#import whisper
import uuid
import torch
import wave
import os
import threading
import tempfile
import src.custom_speech_recognition as sr
import io
from datetime import timedelta
import pyaudiowpatch as pyaudio
from heapq import merge
from datetime import datetime
import time
from .config import AudioConfig, SystemConfig


# Константы для управления обработкой фраз
PHRASE_TIMEOUT = 5.2  # Таймаут фразы по умолчанию
MAX_PHRASE_TIMEOUT = 30.2 # Максимальный таймаут фразы
MAX_PHRASES = 9999 # Максимальное количество фраз (вероятно, не используется активно)

class AudioTranscriber:
    """
    Класс для транскрибации аудио с микрофона и системных звуков (динамика).
    Управляет сбором аудиоданных, их обработкой и обновлением структуры транскрипции.
    """
    def __init__(self, mic_source, speaker_source, model, response_manager):
        # Добавляем response_manager для управления ответами
        self.response_manager = response_manager
        self.transcript_data = {"You": [], "Speaker": []} # Неструктурированные данные транскрипции
        self.structured_transcript = {
            "you": [],      # [(текст, временная_метка, id_ответа), ...] для пользователя
            "speaker": [],  # [(текст, временная_метка, id_ответа), ...] для динамика
            "combined": []  # [(текст, временная_метка, id_ответа, тип_говорящего), ...] для объединенной истории
        }        
        self.len_speaker = 0 # Длина данных спикера (возможно, устарело или используется специфично)
        self.transcript_changed_event = threading.Event() # Событие для сигнализации об изменении транскрипции
        self.audio_model = model # Модель для транскрибации аудио
        self.audio_sources = {
            "You": { # Источник "Вы" (микрофон)
                "sample_rate": mic_source.SAMPLE_RATE,
                "sample_width": mic_source.SAMPLE_WIDTH,
                "channels": mic_source.channels,
                "last_sample": bytes(), # Последний необработанный семпл
                "saved_sample": bytes(), # Сохраненный семпл для обработки
                "chunks_buffer": [],  # Буфер для аудиочанков
                "last_spoken": None, # Время последнего говорения
                "first_spoken": None, # Время первого говорения в текущей фразе
                "new_phrase": True, # Флаг новой фразы
                "process_data_func": self.process_mic_data # Функция обработки данных для этого источника
            },
            "Speaker": { # Источник "Динамик" (системные звуки)
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "saved_sample": bytes(),
                "chunks_buffer": [],
                "last_spoken": None,
                "first_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_speaker_data
            }
        }

    def transcribe_audio_queue(self, audio_queue):
        """Обрабатывает очередь аудиоданных, транскрибирует их и обновляет транскрипцию."""
        while True:
            #print("Отладка: "+ "-----" +"\n")
            who_spoke, data, time_spoken = audio_queue.get() # Получение данных из очереди
            self.update_last_sample_and_phrase_status(who_spoke, data, time_spoken) # Обновление семплов и статуса фразы
            source_info = self.audio_sources[who_spoke]
            text = ''
            try:
                fd, path = tempfile.mkstemp(suffix=".wav") # Создание временного wav-файла
                os.close(fd)
                source_info["process_data_func"](source_info["saved_sample"], path) # Обработка и сохранение данных в файл
                text = self.audio_model.get_transcription(path) # Получение транскрипции
            except Exception as e:
                print(f"Ошибка транскрибации: {e}")
            finally:
                if os.path.exists(path):
                    os.unlink(path) # Удаление временного файла
            
            if text != '' and text.lower() != 'you': # Проверка, что текст не пустой и не "you" (артефакт?)
                print("Перехвачено: "+ text+"\n")
                ## Если текст заканчивается определенным символом, установить как новую фразу (логика не завершена в комментарии)
                # Проверка на таймаут фразы для определения новой фразы
                if (source_info["first_spoken"] and time_spoken - source_info["first_spoken"] > timedelta(seconds=AudioConfig.get_phrase_timeout())) :
                    print ("Новая фраза......\n")
                    source_info["new_phrase"] = True
                    #if who_spoke.lower() == 'speaker': # Условие для события изменения транскрипции (закомментировано)
                        #self.transcript_changed_event.set()
                self.update_transcript(who_spoke, text, time_spoken) # Обновление транскрипции
            else:
                # Ожидание, если текст пустой (возможно, для уменьшения нагрузки)
                print("\r "+who_spoke+" текст: Null, Новая_Фраза:"+str(source_info["new_phrase"])+"\r\n")
                #self.transcript_changed_event.wait(1.5)

    def update_last_sample_and_phrase_status(self, who_spoke, data, time_spoken):
        """Обновляет последний семпл, буфер чанков и статус фразы для указанного источника."""
        source_info = self.audio_sources[who_spoke]
        #print("#1 "+who_spoke+" Сейчас:"+str(time_spoken)+" Начало:"+str(source_info["first_spoken"])+" Конец:"+str(source_info["last_spoken"])+"\r\n")
        
        # Обновление буфера чанков
        max_chunks = AudioConfig.get_buffer_chunks()
        if max_chunks > 0:  # Обработка только если буфер нужен
            source_info["chunks_buffer"].append(data)
            # Поддержание размера буфера не более ограничения
            if len(source_info["chunks_buffer"]) > max_chunks:
                source_info["chunks_buffer"].pop(0)  # Удаление самого старого чанка
        
        if source_info["first_spoken"] == None: # Если это начало новой фразы
                source_info["first_spoken"] = time_spoken
        source_info["last_sample"] += data # Добавление новых данных к последнему семплу
        source_info["last_spoken"] = time_spoken # Обновление времени последнего говорения
        source_info["saved_sample"] = source_info["last_sample"] # Сохранение полного семпла для обработки

    def process_mic_data(self, data, temp_file_name):
        """Обрабатывает данные с микрофона и сохраняет их в WAV файл."""
        audio_data = sr.AudioData(data, self.audio_sources["You"]["sample_rate"], self.audio_sources["You"]["sample_width"])
        wav_data = io.BytesIO(audio_data.get_wav_data())
        with open(temp_file_name, 'w+b') as f:
            f.write(wav_data.read())

    def process_speaker_data(self, data, temp_file_name):
        """Обрабатывает данные с динамика и сохраняет их в WAV файл."""
        with wave.open(temp_file_name, 'wb') as wf:
            wf.setnchannels(self.audio_sources["Speaker"]["channels"])
            p = pyaudio.PyAudio()
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)) # Установка ширины семпла
            wf.setframerate(self.audio_sources["Speaker"]["sample_rate"])
            wf.writeframes(data)

    def update_transcript(self, who_spoke, text, time_spoken):
        """Обновляет различные структуры данных транскрипции на основе нового текста."""
        source_info = self.audio_sources[who_spoke]
        speaker_type = who_spoke.lower()
        
        # Создание записи ответа для ввода пользователя (если это 'speaker' и новая фраза)
        response_id = None
        if speaker_type == 'speaker' and source_info["new_phrase"]:
            #print(f"\nОтладка AudioTranscriber - Новый ввод от Динамика:")
            #print(f"Текст: {text}")
            
            response_id = self.response_manager.create_response(
                question_time=time_spoken,
                question_text=text
            )
            #print(f"Создан новый response_id: {response_id}")
        
        # Создание унифицированной структуры записи
        record = {
            'transcript': (f"{who_spoke}: [{text}]\n\n", time_spoken), # Для простого отображения
            'structured': (text, time_spoken, response_id), # Структурированные данные
            'combined': (text, time_spoken, response_id, speaker_type) # Для объединенного отображения
        }
        #print (f"Новая запись: {record}")
        
        # Обновление структур данных: вставка новой записи или обновление существующей
        update_method = 'insert' if source_info["new_phrase"] or not self.transcript_data[who_spoke] else 'update'
        self._update_all_transcripts(speaker_type, record, update_method)
        
        # Обработка обновления статуса новой фразы
        if source_info["new_phrase"]:
            # Если это ввод от спикера, создан response_id и не включен режим "только запись",
            # то после обновления данных вызывается событие.
            if speaker_type == 'speaker' and response_id and not SystemConfig.get_record_only_mode():
                print("Установка transcript_changed_event после обновления данных")
                self.transcript_changed_event.set()
                
            self._reset_source_info(source_info, time_spoken) # Сброс информации об источнике

    def _reset_source_info(self, source_info, time_spoken):
        """Сбрасывает состояние информации об источнике для начала новой фразы."""
        buffered_data = b''.join(source_info["chunks_buffer"]) if source_info["chunks_buffer"] else bytes()
        source_info.update({
            'first_spoken': time_spoken,
            'last_sample': buffered_data,  # Использование объединенных данных из буфера
            'new_phrase': False,
            'chunks_buffer': []  # Сброс буфера чанков
        })
        print('Данные сброшены с использованием буфера.....\n')

    def _update_all_transcripts(self, speaker_type, record, method='insert'):
        """Обновляет все структуры данных транскрипции (обычную, структурированную, комбинированную)."""
        #print(f"\nОтладка _update_all_transcripts:")
        #print(f"Тип говорящего: {speaker_type}")
        #print(f"Метод: {method}")
        #print(f"ID ответа в записи: {record['structured'][2]}")
        
        index = 0 if method == 'insert' else 0 # Индекс для вставки/обновления (обычно начало списка)
        
        # Если это операция обновления, необходимо сохранить исходный response_id
        if method == 'update' and self.structured_transcript[speaker_type]:
            original_response_id = self.structured_transcript[speaker_type][0][2]
            # Использование исходного response_id для создания нового кортежа записи
            record = {
                'transcript': record['transcript'],
                'structured': (record['structured'][0], record['structured'][1], original_response_id),
                'combined': (record['combined'][0], record['combined'][1], original_response_id, record['combined'][3])
            }
            #print(f"Сохраненный response_id при обновлении: {original_response_id}")
        
        # Обновление исходной транскрипции
        if method == 'insert':
            self.transcript_data[speaker_type.title()].insert(index, record['transcript'])
        else:
            if self.transcript_data[speaker_type.title()]:
                self.transcript_data[speaker_type.title()][index] = record['transcript']
            else: # Если список пуст, вставляем
                self.transcript_data[speaker_type.title()].insert(index, record['transcript'])
        
        # Обновление структурированных данных
        if method == 'insert':
            self.structured_transcript[speaker_type].insert(index, record['structured'])
        else:
            if self.structured_transcript[speaker_type]:
                self.structured_transcript[speaker_type][index] = record['structured']
            else: # Если список пуст, вставляем
                self.structured_transcript[speaker_type].insert(index, record['structured'])
        
        # Обновление комбинированного представления
        if method == 'insert':
            self.structured_transcript['combined'].insert(index, record['combined'])
        else:
            if self.structured_transcript['combined']:
                # Поиск и обновление последнего сообщения для соответствующего speaker_type
                # Это предполагает, что мы обновляем только самое последнее сообщение говорящего в комбинированном списке.
                # Возможно, потребуется более сложная логика для поиска конкретного сообщения для обновления.
                updated_in_combined = False
                for i, msg in reversed(list(enumerate(self.structured_transcript['combined']))): # Ищем с конца
                    if msg[3] == speaker_type:  # Проверка типа говорящего
                        self.structured_transcript['combined'][i] = record['combined']
                        updated_in_combined = True
                        break
                if not updated_in_combined: # Если не найдено (маловероятно при 'update'), вставляем
                     self.structured_transcript['combined'].insert(index, record['combined'])
            else: # Если список пуст, вставляем
                self.structured_transcript['combined'].insert(index, record['combined'])
        
        #print(f"После обновления:")
        #print(f"Количество комбинированных сообщений: {len(self.structured_transcript['combined'])}")
        #if self.structured_transcript['combined']:
        #    print(f"ID ответа последнего комбинированного сообщения: {self.structured_transcript['combined'][0][2]}")
        #    print(f"Вопрос последнего комбинированного сообщения: {self.structured_transcript['combined'][0][0]}")


    def get_transcript(self):
        """Возвращает отформатированные данные транскрипции для отображения."""
        # Возвращает структурированные данные транскрипции
        return {
            'all': "".join([f"{t[3].title()}: [{t[0]}]\n\n" for t in self.structured_transcript["combined"]]),
            'speaker': [{'text': t[0], 'timestamp': t[1], 'response_id': t[2]} 
                       for t in self.structured_transcript["speaker"]],
            'you': [{'text': t[0], 'timestamp': t[1], 'response_id': t[2]} 
                    for t in self.structured_transcript["you"]]
        }

    def get_lastContent(self):
        """Получает содержимое последней записи от "Speaker"."""
        try:
            # Получение последней записи спикера из structured_transcript
            if self.structured_transcript["speaker"]:
                # Формат в structured_transcript: (текст, временная_метка, id_ответа)
                return self.structured_transcript["speaker"][0][0]
            return ''
        except Exception as e:
            print(f"Ошибка в get_lastContent: {e}")
            return ''

    def clear_transcript_data(self):
        """Очищает все данные транскрипции и сбрасывает состояние источников аудио."""
        self.transcript_data["You"].clear()
        self.transcript_data["Speaker"].clear()
        self.structured_transcript["you"].clear()
        self.structured_transcript["speaker"].clear()
        self.structured_transcript["combined"].clear()

        for source_name, source_info in self.audio_sources.items():
            source_info["last_sample"] = bytes()
            source_info["saved_sample"] = bytes()
            source_info["chunks_buffer"].clear()  # Очистка буфера чанков
            source_info["new_phrase"] = True
            source_info["last_spoken"] = None
            source_info["first_spoken"] = None