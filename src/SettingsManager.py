# src/settings_manager.py

import json
import os
from typing import Dict, Any, Optional
from .config import PathConfig

class SettingsManager:
    """Управляет сохранением и загрузкой настроек приложения."""
    
    DEFAULT_SETTINGS = {
        "phrase_timeout": 5.2,         # Таймаут фразы
        "buffer_chunks": 1,            # Количество чанков в буфере
        "update_interval": 2,          # Интервал обновления
        "system_role": "inbound_cs",   # Системная роль
        "case_detail": "inbound_cs",   # Детали случая
        "knowledge": "none",           # База знаний
        "window_opacity": 1.0,         # Непрозрачность окна
        "window_topmost": False,       # Окно поверх всех
        "record_only_mode": False      # Добавлен новый параметр: режим "только запись"
    }
    
    def __init__(self):
        """Инициализирует менеджер настроек."""
        # Использование PathConfig для получения каталога конфигурации
        self.config_dir = PathConfig.get_config_path()
        os.makedirs(self.config_dir, exist_ok=True) # Создание каталога, если он не существует
        
        # Полный путь к файлу настроек
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # Попытка миграции настроек из старого местоположения
        self._migrate_old_settings()
        
        # Загрузка настроек
        self.settings = self.load_settings()
        
        if self.debug_mode:
            print(f"Расположение файла настроек: {self.settings_file}")
    
    def _migrate_old_settings(self):
        """Переносит файл настроек из старой версии."""
        old_config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        old_settings_file = os.path.join(old_config_dir, "settings.json")
        
        if os.path.exists(old_settings_file) and not os.path.exists(self.settings_file):
            try:
                # Чтение старых настроек
                with open(old_settings_file, 'r', encoding='utf-8') as f:
                    old_settings = json.load(f)
                
                # Сохранение в новое местоположение
                os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(old_settings, f, indent=4)
                    
                print(f"Настройки перенесены из {old_settings_file} в {self.settings_file}")
            except Exception as e:
                print(f"Ошибка при переносе настроек: {e}")
            
    def load_settings(self) -> Dict[str, Any]:
        """
        Загружает настройки из файла.
        
        Returns:
            Dict[str, Any]: Словарь настроек.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # Объединение сохраненных настроек с настройками по умолчанию,
                    # чтобы убедиться, что все необходимые ключи существуют.
                    merged_settings = self.DEFAULT_SETTINGS.copy()
                    merged_settings.update(saved_settings)
                    return merged_settings
            return self.DEFAULT_SETTINGS.copy() # Возврат настроек по умолчанию, если файл не найден
        except Exception as e:
            print(f"Ошибка загрузки настроек из {self.settings_file}: {e}")
            return self.DEFAULT_SETTINGS.copy() # Возврат настроек по умолчанию в случае ошибки
            
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки в файл.
        
        Args:
            settings: Словарь настроек для сохранения.
            
        Returns:
            bool: True в случае успешного сохранения, иначе False.
        """
        try:
            # Убедиться, что каталог конфигурации существует
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            self.settings = settings # Обновление текущих настроек в памяти
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек в {self.settings_file}: {e}")
            return False
            
    def get_setting(self, key: str) -> Any:
        """
        Получает значение указанной настройки.
        
        Args:
            key: Имя ключа настройки.
            
        Returns:
            Any: Значение настройки, или значение по умолчанию, если ключ не найден.
        """
        return self.settings.get(key, self.DEFAULT_SETTINGS.get(key))
        
    def update_setting(self, key: str, value: Any) -> bool:
        """
        Обновляет значение указанной настройки.
        
        Args:
            key: Имя ключа настройки.
            value: Новое значение настройки.
            
        Returns:
            bool: True в случае успешного обновления, иначе False.
        """
        try:
            # Преобразование типа для обеспечения соответствия типу значения по умолчанию
            if key in self.DEFAULT_SETTINGS:
                default_value = self.DEFAULT_SETTINGS[key]
                if default_value is not None: # Проверка, что значение по умолчанию не None
                    value = type(default_value)(value)
            self.settings[key] = value
            return self.save_settings(self.settings)
        except Exception as e:
            print(f"Ошибка обновления настройки {key}: {e}")
            return False
    
    @property
    def debug_mode(self) -> bool:
        """Включен ли режим отладки."""
        return False  # Можно изменить при необходимости