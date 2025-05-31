import sqlite3
import os
from datetime import datetime, timedelta

from tools.logger import Logger

logger = Logger.get_instance()

class GroupDatabase:
    """Класс для работы с базой данных сообщений групп"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Получение единственного экземпляра класса (Singleton)"""
        if cls._instance is None:
            cls._instance = GroupDatabase()
        return cls._instance
    
    def __init__(self, db_file="database/group.db"):
        """Инициализация соединения с базой данных"""
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        try:
            self.conn = sqlite3.connect(db_file)
            self.conn.execute("PRAGMA foreign_keys = ON")  # Включаем поддержку внешних ключей
            self.cursor = self.conn.cursor()
            
            # Создаем необходимые таблицы
            self.create_tables()
            
            logger.info(f"Соединение с базой данных групп установлено: {db_file}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к базе данных групп: {e}", exc_info=True)
    
    def create_tables(self):
        """Создание необходимых таблиц в базе данных"""
        try:
            # Таблица для хранения групп сообщений
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    creator_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scheduled_deletion TIMESTAMP NOT NULL
                )
            ''')
            
            self.conn.commit()
            logger.info("Таблицы для сообщений групп созданы или уже существуют")
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблиц для сообщений групп: {e}", exc_info=True)
    
    def save_message(self, group_id, message_id, channel_id, message_type, creator_id, minutes_to_delete=5):
        """Сохраняет данные о сообщении группы"""
        try:
            # Вычисляем время планируемого удаления
            deletion_time = datetime.now() + timedelta(minutes=minutes_to_delete)
            deletion_time_str = deletion_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Сохраняем сообщение
            self.cursor.execute('''
                INSERT INTO group_messages 
                (group_id, message_id, channel_id, type, creator_id, scheduled_deletion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                group_id,
                str(message_id),
                str(channel_id),
                message_type,
                str(creator_id),
                deletion_time_str
            ))
            
            self.conn.commit()
            logger.info(f"Сообщение группы с ID {message_id} сохранено в базе данных (удаление в {deletion_time_str})")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения сообщения группы {message_id}: {e}", exc_info=True)
            return False
    
    def get_messages_to_delete(self):
        """Получает сообщения, которые пора удалить"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.cursor.execute('''
                SELECT group_id, message_id, channel_id
                FROM group_messages
                WHERE scheduled_deletion <= ?
            ''', (current_time,))
            
            messages = self.cursor.fetchall()
            return messages
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения сообщений для удаления: {e}", exc_info=True)
            return []
    
    def delete_message_record(self, message_id):
        """Удаляет запись о сообщении из базы данных"""
        try:
            self.cursor.execute("DELETE FROM group_messages WHERE message_id = ?", (message_id,))
            self.conn.commit()
            logger.info(f"Запись о сообщении группы с ID {message_id} удалена из базы данных")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления записи о сообщении группы {message_id}: {e}", exc_info=True)
            return False
    
    def get_group_messages(self, group_id):
        """Получает все сообщения определенной группы"""
        try:
            self.cursor.execute('''
                SELECT message_id, channel_id, scheduled_deletion
                FROM group_messages
                WHERE group_id = ?
            ''', (group_id,))
            
            messages = self.cursor.fetchall()
            return messages
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения сообщений группы {group_id}: {e}", exc_info=True)
            return []
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных групп закрыто") 