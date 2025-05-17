import sqlite3
import json
import os
from datetime import datetime
from tools.logger import Logger

logger = Logger.get_instance()

class CaptDatabase:
    """Класс для работы с базой данных сборов игроков"""
    
    DB_PATH = "database/capt.db"
    
    def __init__(self):
        """Инициализация и создание таблиц, если они не существуют"""
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
    def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = sqlite3.connect(self.DB_PATH)
            self.cursor = self.conn.cursor()
            logger.info(f"Подключение к базе данных сборов установлено: {self.DB_PATH}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к базе данных сборов: {e}", exc_info=True)
    
    def create_tables(self):
        """Создание необходимых таблиц в базе данных"""
        try:
            # Таблица сборов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS capts (
                    message_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    creator_id TEXT NOT NULL,
                    creator_name TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    slots INTEGER NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    thread_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица участников
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    is_extra BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY (message_id) REFERENCES capts (message_id) ON DELETE CASCADE
                )
            ''')
            
            self.conn.commit()
            logger.info("Таблицы для сборов созданы или уже существуют")
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблиц для сборов: {e}", exc_info=True)
    
    def save_capt(self, message_id, capt_data):
        """Сохраняет или обновляет данные сбора"""
        try:
            # Проверяем существование сбора
            self.cursor.execute("SELECT message_id FROM capts WHERE message_id = ?", (message_id,))
            exists = self.cursor.fetchone()
            
            if exists:
                # Обновляем существующий сбор
                self.cursor.execute('''
                    UPDATE capts 
                    SET name = ?, creator_id = ?, creator_name = ?, datetime = ?, slots = ?, thread_id = ?
                    WHERE message_id = ?
                ''', (
                    capt_data['name'],
                    str(capt_data['creator'].id),
                    capt_data['creator'].display_name,
                    capt_data['datetime'],
                    capt_data['slots'],
                    str(capt_data.get('thread_id', '')),
                    message_id
                ))
            else:
                # Создаем новый сбор
                self.cursor.execute('''
                    INSERT INTO capts (message_id, name, creator_id, creator_name, datetime, slots, guild_id, channel_id, thread_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message_id,
                    capt_data['name'],
                    str(capt_data['creator'].id),
                    capt_data['creator'].display_name,
                    capt_data['datetime'],
                    capt_data['slots'],
                    str(capt_data['guild_id']),
                    str(capt_data['channel_id']),
                    str(capt_data.get('thread_id', ''))
                ))
            
            # Удаляем старых участников
            self.cursor.execute("DELETE FROM participants WHERE message_id = ?", (message_id,))
            
            # Добавляем основных участников
            for participant in capt_data['participants']:
                self.cursor.execute('''
                    INSERT INTO participants (message_id, user_id, user_name, is_extra)
                    VALUES (?, ?, ?, 0)
                ''', (
                    message_id,
                    str(participant.id),
                    participant.display_name
                ))
            
            # Добавляем дополнительных участников
            for participant in capt_data['extra_participants']:
                self.cursor.execute('''
                    INSERT INTO participants (message_id, user_id, user_name, is_extra)
                    VALUES (?, ?, ?, 1)
                ''', (
                    message_id,
                    str(participant.id),
                    participant.display_name
                ))
            
            self.conn.commit()
            logger.info(f"Сбор с ID {message_id} сохранен в базе данных")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения сбора {message_id}: {e}", exc_info=True)
            return False
    
    def get_capt(self, message_id):
        """Получает данные сбора из базы данных"""
        try:
            # Получаем основные данные
            self.cursor.execute('''
                SELECT message_id, name, creator_id, creator_name, datetime, slots, guild_id, channel_id, thread_id
                FROM capts WHERE message_id = ?
            ''', (message_id,))
            
            capt_row = self.cursor.fetchone()
            if not capt_row:
                return None
            
            # Формируем базовую структуру
            capt_info = {
                "message_id": capt_row[0],
                "name": capt_row[1],
                "creator": {
                    "id": capt_row[2],
                    "name": capt_row[3]
                },
                "datetime": capt_row[4],
                "slots": capt_row[5],
                "guild_id": capt_row[6],
                "channel_id": capt_row[7],
                "thread_id": capt_row[8] if capt_row[8] else None,
                "participants": [],
                "extra_participants": []
            }
            
            # Получаем участников
            self.cursor.execute('''
                SELECT user_id, user_name, is_extra
                FROM participants WHERE message_id = ?
            ''', (message_id,))
            
            for participant in self.cursor.fetchall():
                participant_info = {
                    "id": participant[0],
                    "name": participant[1]
                }
                
                if participant[2]:  # is_extra
                    capt_info["extra_participants"].append(participant_info)
                else:
                    capt_info["participants"].append(participant_info)
            
            return capt_info
        
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения сбора {message_id}: {e}", exc_info=True)
            return None
    
    def get_all_capts(self):
        """Получает все активные сборы из базы данных"""
        try:
            # Получаем все ID сборов
            self.cursor.execute("SELECT message_id FROM capts")
            capt_ids = self.cursor.fetchall()
            
            result = {}
            for (message_id,) in capt_ids:
                capt_info = self.get_capt(message_id)
                if capt_info:
                    result[message_id] = capt_info
            
            return result
        
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения всех сборов: {e}", exc_info=True)
            return {}
    
    def delete_capt(self, message_id):
        """Удаляет сбор из базы данных"""
        try:
            # Каскадное удаление удалит и всех участников
            self.cursor.execute("DELETE FROM capts WHERE message_id = ?", (message_id,))
            self.conn.commit()
            logger.info(f"Сбор с ID {message_id} удален из базы данных")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления сбора {message_id}: {e}", exc_info=True)
            return False
    
    def clean_old_capts(self, days=7):
        """Удаляет старые сборы"""
        try:
            # Формируем запрос с конкретным значением дней
            days_str = f"-{days} days"
            self.cursor.execute(f'''
                DELETE FROM capts
                WHERE datetime('now', ?) > datetime(created_at)
            ''', (days_str,))
            
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Удалено {deleted_count} старых сборов (старше {days} дней)")
            
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Ошибка при очистке старых сборов: {e}", exc_info=True)
            return 0
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных сборов закрыто")

# Создаем синглтон для работы с базой данных
_instance = None

def get_instance():
    """Получает экземпляр базы данных сборов"""
    global _instance
    if _instance is None:
        _instance = CaptDatabase()
    return _instance 