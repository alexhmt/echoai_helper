# src/config.py

import os
import sys
from dotenv import load_dotenv
from typing import Optional

class PathConfig:
    """Управление конфигурацией путей"""
    
    @staticmethod
    def get_project_root():
        """Получить корневой каталог проекта"""
        if getattr(sys, 'frozen', False):
            # Каталог исполняемого файла после упаковки
            return os.path.dirname(sys.executable)
        else:
            # Корневой каталог проекта в среде разработки (родительский каталог src)
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @staticmethod
    def get_resource_path():
        """Получить каталог файлов ресурсов"""
        if getattr(sys, 'frozen', False):
            # Каталог ресурсов после упаковки
            return os.path.join(sys._MEIPASS, 'resources')
        else:
            # Каталог ресурсов в среде разработки
            return os.path.join(PathConfig.get_project_root(), 'resources')
    
    @staticmethod
    def get_config_path():
        """Получить каталог конфигурационных файлов"""
        return os.path.join(PathConfig.get_resource_path(), 'config')
    
    @staticmethod
    def get_prompt_path():
        """Получить каталог для prompt'ов"""
        return os.path.join(PathConfig.get_resource_path(), 'prompt')

    @staticmethod
    def get_templates_path():
        """Получить каталог шаблонов"""
        return os.path.join(PathConfig.get_resource_path(), 'templates')
        
    @staticmethod
    def get_models_path():
        """Получить каталог файлов моделей"""
        return os.path.join(PathConfig.get_resource_path(), 'models')

class EnvConfig:
    """Класс управления конфигурацией окружения"""
    
    _instance = None
    _initialized = False
    _llm_provider = "openai"  # Провайдер LLM по умолчанию
    _llm_api_base_url = None  # Базовый URL API по умолчанию (опционально)
    _llm_model_name = "gpt-4o-mini"  # Имя модели по умолчанию
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls) -> None:
        """Инициализировать конфигурацию окружения"""
        if cls._initialized:
            return
        
        # Получить путь к файлу .env
        env_path = os.path.join(PathConfig.get_project_root(), '.env')
        
        # Если файл .env не существует, создать его
        if not os.path.exists(env_path):
            cls.create_env_template(env_path)
            print(f"Пожалуйста, установите ваш OpenAI API ключ в {env_path}")
            return
        
        # Загрузить файл .env
        load_dotenv(env_path)
        
        # Загрузить конфигурацию LLM из переменных окружения
        cls._llm_provider = os.getenv('LLM_PROVIDER', cls._llm_provider)
        cls._llm_api_base_url = os.getenv('LLM_API_BASE_URL', cls._llm_api_base_url)
        cls._llm_model_name = os.getenv('LLM_MODEL_NAME', cls._llm_model_name)

        # Проверить API ключ
        if cls._llm_provider == "openai" and not os.getenv('OPENAI_API_KEY'):
            print(f"OPENAI_API_KEY не найден в {env_path} (требуется для провайдера OpenAI)")
            print("Пожалуйста, добавьте ваш OpenAI API ключ в файл .env")
            return
        
        cls._initialized = True
    
    @classmethod
    def create_env_template(cls, env_path: str) -> None:
        """Создать шаблон файла .env"""
        template = (
            "# Конфигурация OpenAI API\n"
            "OPENAI_API_KEY=your_api_key_here\n"
            "\n"
            "# Конфигурация LLM (опционально)\n"
            "# LLM_PROVIDER: Используемый провайдер LLM (например, 'openai', 'custom'). По умолчанию: 'openai'\n"
            "LLM_PROVIDER=openai\n"
            "# LLM_API_BASE_URL: Пользовательский базовый URL API для провайдера LLM (например, для локальных LLM). Опционально.\n"
            "# LLM_API_BASE_URL=\n"
            "# LLM_MODEL_NAME: Конкретное имя модели для использования. По умолчанию: 'gpt-4o-mini'\n"
            "LLM_MODEL_NAME=gpt-4o-mini\n"
            "\n"
            "# Добавьте другие переменные конфигурации ниже\n"
        )
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(template)
            print(f"Создан шаблон файла .env по адресу {env_path}")
        except Exception as e:
            print(f"Ошибка при создании шаблона .env: {e}")
    
    @classmethod
    def get_openai_key(cls) -> Optional[str]:
        if not cls._initialized:
            cls.initialize()
        return os.getenv('OPENAI_API_KEY')

    @classmethod
    def get_llm_provider(cls) -> str:
        if not cls._initialized:
            cls.initialize()
        return cls._llm_provider

    @classmethod
    def get_llm_api_base_url(cls) -> Optional[str]:
        if not cls._initialized:
            cls.initialize()
        return cls._llm_api_base_url

    @classmethod
    def get_llm_model_name(cls) -> str:
        if not cls._initialized:
            cls.initialize()
        return cls._llm_model_name
    
    @classmethod
    def ensure_api_key(cls) -> bool:
        # Эта проверка теперь более детализирована; зависит от провайдера
        if cls.get_llm_provider() == "openai":
            api_key = cls.get_openai_key()
            return bool(api_key and api_key != 'your_api_key_here')
        # Для других провайдеров API-ключ может не называться 'OPENAI_API_KEY' или может не требоваться
        return True

class SystemConfig:
    _instance = None
    _system_role = ""
    _record_only_mode = False  # Добавить новую переменную класса для режима "только запись"

    @classmethod
    def get_system_role(cls):
        return cls._system_role

    @classmethod
    def set_system_role(cls, role):
        cls._system_role = role
    @classmethod
    def get_record_only_mode(cls):
        """Получить текущее состояние режима 'только запись'"""
        return cls._record_only_mode

    @classmethod
    def set_record_only_mode(cls, value: bool):
        """Установить состояние режима 'только запись'
        
        Args:
            value (bool): True для включения режима 'только запись', False для выключения
        """
        cls._record_only_mode = bool(value)
        
class AudioConfig:
    _instance = None
    _phrase_timeout = 5.2  # Значение по умолчанию
    _buffer_chunks = 1     # Значение по умолчанию

    @classmethod
    def get_buffer_chunks(cls):
        return cls._buffer_chunks

    @classmethod
    def set_buffer_chunks(cls, value):
        try:
            value = int(value)
            if 0 <= value <= 10:
                cls._buffer_chunks = value
                return True
            return False
        except ValueError:
            return False

    @classmethod
    def get_phrase_timeout(cls):
        return cls._phrase_timeout

    @classmethod
    def set_phrase_timeout(cls, value):
        try:
            value = float(value)
            if 0.01 <= value <= 50:
                cls._phrase_timeout = value
                return True
            return False
        except ValueError:
            return False