"""
Конфигурация характеристик персонажа для Dungeons & Dragons 5e
"""

CHARACTER_STATS = {
    # Основные характеристики
    "abilities": {
        "strength": {
            "name": "Сила",
            "description": "Физическая сила и атлетические способности",
            "skills": ["Атлетика"],
            "value": 10,
            "modifier": 0,
            "saving_throw_proficient": False
        },
        "dexterity": {
            "name": "Ловкость",
            "description": "Координация, рефлексы и равновесие",
            "skills": ["Акробатика", "Ловкость рук", "Скрытность"],
            "value": 10,
            "modifier": 0,
            "saving_throw_proficient": False
        },
        "constitution": {
            "name": "Телосложение",
            "description": "Здоровье, выносливость и жизненная сила",
            "skills": [],
            "value": 10,
            "modifier": 0,
            "saving_throw_proficient": False
        },
        "intelligence": {
            "name": "Интеллект",
            "description": "Умственные способности, память и логика",
            "skills": ["Анализ", "История", "Магия", "Природа", "Религия"],
            "value": 10,
            "modifier": 0,
            "saving_throw_proficient": False
        },
        "wisdom": {
            "name": "Мудрость",
            "description": "Восприятие, интуиция и проницательность",
            "skills": ["Восприятие", "Выживание", "Медицина", "Проницательность", "Уход за животными"],
            "value": 10,
            "modifier": 0,
            "saving_throw_proficient": False
        },
        "charisma": {
            "name": "Харизма",
            "description": "Сила личности, убеждение и лидерство",
            "skills": ["Запугивание", "Обман", "Убеждение", "Выступление"],
            "value": 10,
            "modifier": 0,
            "saving_throw_proficient": False
        }
    },
    
    # Базовые параметры
    "base_stats": {
        "hit_points": {
            "name": "Хиты",
            "description": "Количество очков здоровья",
            "maximum": 0,
            "current": 0,
            "temporary": 0
        },
        "armor_class": {
            "name": "Класс брони",
            "description": "Защита от атак",
            "value": 10,
            "base": 10,
            "bonus": 0
        },
        "proficiency_bonus": {
            "name": "Бонус мастерства",
            "description": "Бонус к проверкам характеристик и атакам",
            "value": 2
        },
        "speed": {
            "name": "Скорость",
            "description": "Базовая скорость передвижения",
            "base": 30,
            "current": 30,
            "fly": 0,
            "swim": 0,
            "climb": 0,
            "burrow": 0
        }
    },
    
    # Расширенные параметры
    "advanced_stats": {
        "saving_throws": {
            "name": "Спасброски",
            "description": "Базовые спасброски по характеристикам",
            "values": {
                "strength": 0,
                "dexterity": 0,
                "constitution": 0,
                "intelligence": 0,
                "wisdom": 0,
                "charisma": 0
            }
        },
        "skills": {
            "name": "Навыки",
            "description": "Все доступные навыки персонажа",
            "proficiencies": [],
            "expertise": [],
            "values": {
                "Атлетика": 0,
                "Акробатика": 0,
                "Ловкость рук": 0,
                "Скрытность": 0,
                "Анализ": 0,
                "История": 0,
                "Магия": 0,
                "Природа": 0,
                "Религия": 0,
                "Восприятие": 0,
                "Выживание": 0,
                "Медицина": 0,
                "Проницательность": 0,
                "Уход за животными": 0,
                "Запугивание": 0,
                "Обман": 0,
                "Убеждение": 0,
                "Выступление": 0
            }
        },
        "resistances": {
            "name": "Сопротивления",
            "description": "Сопротивление к различным типам урона",
            "values": []
        },
        "immunities": {
            "name": "Иммунитеты",
            "description": "Иммунитеты к различным эффектам",
            "values": []
        }
    },
    
    # Инвентарь и снаряжение
    "equipment": {
        "weapons": {
            "name": "Оружие",
            "description": "Вооружение персонажа",
            "items": []
        },
        "armor": {
            "name": "Броня",
            "description": "Защитное снаряжение",
            "items": []
        },
        "items": {
            "name": "Предметы",
            "description": "Различные предметы в инвентаре",
            "items": []
        },
        "money": {
            "name": "Деньги",
            "description": "Валюта и ценности",
            "copper": 0,
            "silver": 0,
            "gold": 0,
            "platinum": 0
        }
    },
    
    # Магические способности
    "magic": {
        "spell_slots": {
            "name": "Ячейки заклинаний",
            "description": "Доступные ячейки для заклинаний",
            "values": {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
                "5": 0,
                "6": 0,
                "7": 0,
                "8": 0,
                "9": 0
            }
        },
        "spells_known": {
            "name": "Известные заклинания",
            "description": "Список известных заклинаний",
            "cantrips": [],
            "spells": []
        },
        "spell_save_dc": {
            "name": "Сложность спасброска",
            "description": "Сложность спасброска от заклинаний",
            "value": 0
        },
        "spell_attack_bonus": {
            "name": "Бонус к атаке заклинаниями",
            "description": "Бонус к броскам атаки заклинаниями",
            "value": 0
        }
    }
} 