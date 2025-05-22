import json
import os
from pathlib import Path
from typing import Dict, Any

class CharacterStorage:
    def __init__(self, base_dir: str = "characters"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def _get_user_dir(self, user_id: int) -> Path:
        """Получить директорию пользователя"""
        user_dir = self.base_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def _get_character_path(self, user_id: int, character_name: str) -> Path:
        """Получить путь к файлу персонажа"""
        user_dir = self._get_user_dir(user_id)
        # Заменяем пробелы и специальные символы на подчеркивания
        safe_name = "".join(c if c.isalnum() else "_" for c in character_name)
        return user_dir / f"{safe_name}.json"
    
    def save_character(self, user_id: int, character_data: Dict[str, Any]) -> bool:
        """Сохранить персонажа в файл"""
        try:
            character_path = self._get_character_path(user_id, character_data["name"])
            
            # Добавляем ID пользователя к данным персонажа
            character_data["user_id"] = user_id
            
            with open(character_path, "w", encoding="utf-8") as f:
                json.dump(character_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении персонажа: {e}")
            return False
    
    def load_character(self, user_id: int, character_name: str) -> Dict[str, Any]:
        """Загрузить персонажа из файла"""
        try:
            character_path = self._get_character_path(user_id, character_name)
            if not character_path.exists():
                return None
            
            with open(character_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке персонажа: {e}")
            return None
    
    def get_user_characters(self, user_id: int) -> list:
        """Получить список всех персонажей пользователя"""
        try:
            user_dir = self._get_user_dir(user_id)
            characters = []
            
            for file_path in user_dir.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    character_data = json.load(f)
                    characters.append(character_data)
            
            return characters
        except Exception as e:
            print(f"Ошибка при получении списка персонажей: {e}")
            return []
    
    def delete_character(self, user_id: int, character_name: str) -> bool:
        """Удалить персонажа"""
        try:
            character_path = self._get_character_path(user_id, character_name)
            if character_path.exists():
                character_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Ошибка при удалении персонажа: {e}")
            return False 