import sqlite3
import os

from utils.logger import Logger

logger = Logger.get_instance()

class DatabaseManager:
    """Класс для управления базой данных SQLite"""

    def __init__(self, db_file="database/reactions.db"):
        self.db_file = db_file
        self.conn = None

        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Инициализация базы данных и создание необходимых таблиц"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            # Создаем таблицу для хранения данных о кнопках реакций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reaction_buttons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    approve_button_id TEXT NOT NULL,
                    reject_button_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Создаем таблицу для хранения логов действий с кнопками
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.conn.commit()
            logger.info(f"База данных инициализирована: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)

    def add_reaction_buttons(self, message_id, channel_id, submission_type, approve_button_id, reject_button_id):
        """
        Добавление информации о кнопках реакции

        Args:
            message_id: ID сообщения с кнопками
            channel_id: ID канала с сообщением
            submission_type: Тип заявки (report/suggestion)
            approve_button_id: ID кнопки одобрения
            reject_button_id: ID кнопки отклонения

        Returns:
            ID записи в базе данных или None в случае ошибки
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT INTO reaction_buttons (message_id, channel_id, type, approve_button_id, reject_button_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(message_id), str(channel_id), submission_type, approve_button_id, reject_button_id))

            self.conn.commit()
            record_id = cursor.lastrowid
            logger.info(f"Добавлены кнопки реакции для сообщения {message_id} в канале {channel_id}")
            return record_id
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении информации о кнопках: {e}", exc_info=True)
            return None
        finally:
            if self.conn:
                self.conn.close()

    def get_all_reaction_buttons(self):
        """
        Получение всех данных о кнопках реакции

        Returns:
            Список словарей с данными о кнопках реакции
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            cursor.execute('SELECT * FROM reaction_buttons')
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'message_id': row['message_id'],
                    'channel_id': row['channel_id'],
                    'type': row['type'],
                    'approve_button_id': row['approve_button_id'],
                    'reject_button_id': row['reject_button_id'],
                    'created_at': row['created_at']
                })

            logger.info(f"Получено {len(result)} записей о кнопках реакции")
            return result
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении данных о кнопках: {e}", exc_info=True)
            return []
        finally:
            if self.conn:
                self.conn.close()

    def delete_reaction_buttons(self, message_id, channel_id):
        """
        Удаление информации о кнопках реакции

        Args:
            message_id: ID сообщения с кнопками
            channel_id: ID канала с сообщением

        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            cursor.execute('''
                DELETE FROM reaction_buttons
                WHERE message_id = ? AND channel_id = ?
            ''', (str(message_id), str(channel_id)))

            self.conn.commit()
            affected_rows = cursor.rowcount
            logger.info(f"Удалено {affected_rows} записей о кнопках реакции для сообщения {message_id}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении информации о кнопках: {e}", exc_info=True)
            return False
        finally:
            if self.conn:
                self.conn.close()

    def get_button_info_by_id(self, button_id):
        """
        Получение информации о кнопке по её ID

        Args:
            button_id: ID кнопки
            
        Returns:
            Словарь с информацией о кнопке или None, если кнопка не найдена
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            cursor.execute('''
                SELECT * FROM reaction_buttons
                WHERE approve_button_id = ? OR reject_button_id = ?
            ''', (button_id, button_id))

            row = cursor.fetchone()

            if row:
                button_info = {
                    'id': row['id'],
                    'message_id': row['message_id'],
                    'channel_id': row['channel_id'],
                    'type': row['type'],
                    'approve_button_id': row['approve_button_id'],
                    'reject_button_id': row['reject_button_id'],
                    'created_at': row['created_at'],
                    'is_approve': row['approve_button_id'] == button_id
                }
                logger.info(f"Найдена информация о кнопке {button_id}")
                return button_info

            logger.warning(f"Кнопка с ID {button_id} не найдена в базе данных")
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении информации о кнопке: {e}", exc_info=True)
            return None
        finally:
            if self.conn:
                self.conn.close()

    def log_reaction_action(self, message_id: int, channel_id: int, user_id: int, 
                          moderator_id: int, action: str, reason: str = None):
        """
        Логирование действия с кнопкой реакции

        Args:
            message_id: ID сообщения
            channel_id: ID канала
            user_id: ID пользователя, создавшего заявку
            moderator_id: ID модератора, выполнившего действие
            action: Действие (approve/reject)
            reason: Причина отклонения (только для reject)

        Returns:
            True, если успешно, False в случае ошибки
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT INTO reaction_logs
                (message_id, channel_id, user_id, moderator_id, action, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, channel_id, user_id, moderator_id, action, reason))

            self.conn.commit()
            logger.info(f"Действие {action} с сообщением {message_id} в канале {channel_id} записано в логи")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при логировании действия с кнопкой реакции: {e}", exc_info=True)
            return False
        finally:
            if self.conn:
                self.conn.close()

    def get_reaction_logs(self, limit: int = 100):
        """
        Получение логов действий с кнопками реакций

        Args:
            limit: Максимальное количество логов для возврата

        Returns:
            Список словарей с информацией о логах
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            cursor.execute('''
                SELECT * FROM reaction_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'message_id': row['message_id'],
                    'channel_id': row['channel_id'],
                    'user_id': row['user_id'],
                    'moderator_id': row['moderator_id'],
                    'action': row['action'],
                    'reason': row['reason'],
                    'timestamp': row['timestamp']
                })

            logger.info(f"Получено {len(result)} записей логов действий с кнопками реакций")
            return result
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении логов действий с кнопками реакций: {e}", exc_info=True)
            return []
        finally:
            if self.conn:
                self.conn.close()

    @classmethod
    def get_instance(cls, db_file="database/reactions.db"):
        """
        Получение глобального экземпляра менеджера базы данных

        Args:
            db_file: Путь к файлу базы данных

        Returns:
            Экземпляр менеджера базы данных
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls(db_file)

        return cls._instance