"""
src/template_manager.py
Класс для управления системными ролями и шаблонами, отвечает за загрузку, обновление и поддержку шаблонов.
"""

import os
import glob
import traceback
from typing import List, Optional, Tuple, Dict
from .SettingsManager import SettingsManager
from .config import SystemConfig, PathConfig

class TemplateManager:
    """Класс менеджера шаблонов, обрабатывает файлы шаблонов, связанные с системными ролями."""
    
    @classmethod
    def _get_template_paths(cls) -> Dict[str, Tuple[str, str]]:
        """Получает конфигурацию путей к шаблонам."""
        prompt_path = PathConfig.get_prompt_path()
        return {
            'system_role': (os.path.join(prompt_path, 'system_role'), '.py'), # Путь к шаблонам системных ролей
            'case_detail': (os.path.join(prompt_path, 'case_detail'), '.txt'), # Путь к шаблонам деталей случая
            'knowledge': (os.path.join(prompt_path, 'knowledge'), '.txt')     # Путь к шаблонам базы знаний
        }
    
    @classmethod
    def initialize_default_role(cls) -> bool:
        """Инициализирует системную роль по умолчанию."""
        try:
            settings_manager = SettingsManager()
            
            # Получение всех доступных файлов шаблонов
            system_role_files = cls.get_template_files('system_role')
            case_detail_files = cls.get_template_files('case_detail')
            knowledge_files = cls.get_template_files('knowledge')
            
            # Получение сохраненных значений из настроек
            saved_role = settings_manager.get_setting("system_role")
            saved_detail = settings_manager.get_setting("case_detail")
            saved_knowledge = settings_manager.get_setting("knowledge")
            
            # Проверка валидности сохраненных значений
            saved_role_valid = saved_role in system_role_files
            saved_detail_valid = saved_detail in case_detail_files
            saved_knowledge_valid = saved_knowledge in knowledge_files
            
            if saved_role_valid and saved_detail_valid and saved_knowledge_valid:
                print(f"Использование сохраненных настроек шаблонов: {saved_role}, {saved_detail}, {saved_knowledge}")
                success = cls.update_system_role(saved_role, saved_detail, saved_knowledge)
                if success:
                    print(f"Роль инициализирована из настроек: {saved_role}")
                    return True
            
            # Использование значений по умолчанию
            print("Использование шаблонов по умолчанию")
            default_role = system_role_files[0] if system_role_files else 'inbound_cs'
            default_detail = case_detail_files[0] if case_detail_files else 'inbound_cs'
            default_knowledge = knowledge_files[0] if knowledge_files else 'none'
            
            success = cls.update_system_role(default_role, default_detail, default_knowledge)
            if success:
                settings_manager.update_setting("system_role", default_role)
                settings_manager.update_setting("case_detail", default_detail)
                settings_manager.update_setting("knowledge", default_knowledge)
                print(f"Роль по умолчанию инициализирована: {default_role}")
                return True
                
            print("Не удалось инициализировать роль по умолчанию")
            return False
            
        except Exception as e:
            print(f"Ошибка при инициализации роли по умолчанию: {e}")
            traceback.print_exc()
            return False

    @classmethod
    def load_template(cls, filepath: str) -> str:
        """Загружает содержимое файла шаблона."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content.strip(): # Проверка, не пуст ли файл
                    print(f"Предупреждение: Файл шаблона пуст: {filepath}")
                return content
        except Exception as e:
            print(f"Ошибка загрузки шаблона {filepath}: {e}")
            traceback.print_exc()
            return ""

    @classmethod
    def get_template_files(cls, category: str) -> List[str]:
        """Получает все файлы шаблонов указанной категории."""
        template_paths = cls._get_template_paths()
        if category not in template_paths:
            print(f"Недопустимая категория шаблона: {category}")
            return []
            
        path, ext = template_paths[category]
        pattern = os.path.join(path, f"*{ext}") # Шаблон для поиска файлов
        
        try:
            # Убедиться, что каталог существует
            os.makedirs(os.path.dirname(pattern), exist_ok=True)
            
            files = glob.glob(pattern)
            # Возвращает список имен файлов без расширения
            return [os.path.basename(f).replace(ext, '') for f in files]
        except Exception as e:
            print(f"Ошибка при получении файлов шаблонов для категории {category}: {e}")
            traceback.print_exc()
            return []

    @classmethod
    def update_system_role(cls, system_role_file: str, case_detail_file: str, 
                          knowledge_file: str) -> Optional[str]:
        """Обновляет конфигурацию системной роли."""
        try:
            template_paths = cls._get_template_paths()
            
            # Формирование полных путей к файлам
            system_role_path = os.path.join(template_paths['system_role'][0], 
                                          f"{system_role_file}{template_paths['system_role'][1]}")
            case_detail_path = os.path.join(template_paths['case_detail'][0], 
                                          f"{case_detail_file}{template_paths['case_detail'][1]}")
            knowledge_path = os.path.join(template_paths['knowledge'][0], 
                                        f"{knowledge_file}{template_paths['knowledge'][1]}")
            
            # Загрузка содержимого шаблонов
            system_role = cls.load_template(system_role_path)
            case_detail = cls.load_template(case_detail_path)
            knowledge = cls.load_template(knowledge_path)
            
            # Проверка, что все шаблоны загружены
            if not all([system_role, case_detail, knowledge]): # Используем all() для краткости
                print("Ошибка: Один или несколько шаблонов не удалось загрузить")
                return None
            
            try:
                # Форматирование системной роли с деталями случая и базой знаний
                new_role = system_role.format(case_detail=case_detail, knowledge=knowledge)
                if new_role.strip():  # Убедиться, что отформатированная роль не пуста
                    SystemConfig.set_system_role(new_role)
                    return new_role
                print("Ошибка: Отформатированная роль пуста")
                return None
            except KeyError as e: # Ошибка, если в шаблоне отсутствует ключ форматирования
                print(f"Ошибка формата шаблона: Отсутствует ключ {e}")
                traceback.print_exc()
                return None
                
        except Exception as e:
            print(f"Ошибка при обновлении системной роли: {e}")
            traceback.print_exc()
            return None

    @classmethod
    def ensure_template_directories(cls) -> None:
        """Гарантирует существование всех каталогов шаблонов."""
        for path, _ in cls._get_template_paths().values():
            try:
                os.makedirs(path, exist_ok=True) # Создание каталога, если он не существует
            except Exception as e:
                print(f"Ошибка при создании каталога {path}: {e}")
                traceback.print_exc()

    @classmethod
    def get_current_role(cls) -> Optional[str]:
        """Получает текущую конфигурацию системной роли."""
        return SystemConfig.get_system_role()