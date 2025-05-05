import sqlite3
import os
import discord
import re
from tools.logger import Logger

logger = Logger.get_instance()

class UserManager:
    """
    Класс для управления базой данных пользователей.
    Сохраняет информацию о пользователях сервера (id и отображаемое имя).
    """

    def __init__(self, db_file="database/user.db"):
        self.db_file = db_file
        self.conn = None

        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Инициализация базы данных и создание необходимых таблиц"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            # Проверяем существует ли таблица пользователей
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone()

            if not table_exists:
                # Создаем таблицу для хранения данных о пользователях
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        game_static TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                logger.info("Создана новая таблица пользователей с полем game_static")
            else:
                # Проверяем, есть ли колонка game_static, и если нет, добавляем ее
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if "game_static" not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN game_static TEXT")
                    logger.info("В существующую таблицу пользователей добавлено поле game_static")

            self.conn.commit()
            logger.info(f"База данных пользователей инициализирована: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при инициализации базы данных пользователей: {e}", exc_info=True)

    def extract_game_static(self, display_name: str) -> str:
        """
        Извлекает игровой статик из отображаемого имени пользователя
        
        Поддерживаемые форматы:
        - Lemird 23134
        - Lemird|23134
        - Lemird (23134)
        - Lemird [23134]
        - Lemird-23134
        - и т.д.
        
        Args:
            display_name: Отображаемое имя пользователя
            
        Returns:
            Строка с игровым статиком или None, если статик не найден
        """
        # Паттерны для поиска статиков в разных форматах
        patterns = [
            r'\s(\d{4,6})\s*$',             # Имя 23134
            r'\|(\d{4,6})\s*$',             # Имя|23134
            r'\((\d{4,6})\)\s*$',           # Имя(23134)
            r'\[(\d{4,6})\]\s*$',           # Имя[23134]
            r'-(\d{4,6})\s*$',              # Имя-23134
            r'#(\d{4,6})\s*$',              # Имя#23134
            r'_(\d{4,6})\s*$',              # Имя_23134
            r'•(\d{4,6})\s*$',              # Имя•23134
            r'\.(\d{4,6})\s*$',             # Имя.23134
            r'\s*(\d{4,6})$'                # Просто цифры в конце
        ]
        
        for pattern in patterns:
            match = re.search(pattern, display_name)
            if match:
                return match.group(1)
        
        return None

    def update_user(self, user_id: int, display_name: str):
        """
        Добавляет или обновляет информацию о пользователе в базе данных

        Args:
            user_id: ID пользователя Discord
            display_name: Отображаемое имя пользователя

        Returns:
            True, если обновление прошло успешно, иначе False
        """
        try:
            # Извлекаем игровой статик из отображаемого имени
            game_static = self.extract_game_static(display_name)
            
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            # Проверяем существует ли уже пользователь
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            exists = cursor.fetchone()

            if exists:
                # Обновляем существующего пользователя
                cursor.execute('''
                    UPDATE users 
                    SET display_name = ?, game_static = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (display_name, game_static, user_id))
                logger.info(f"Обновлен пользователь {display_name} (ID: {user_id}, Статик: {game_static})")
            else:
                # Добавляем нового пользователя
                cursor.execute('''
                    INSERT INTO users (id, display_name, game_static) 
                    VALUES (?, ?, ?)
                ''', (user_id, display_name, game_static))
                logger.info(f"Добавлен новый пользователь {display_name} (ID: {user_id}, Статик: {game_static})")

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении пользователя {display_name} (ID: {user_id}): {e}", exc_info=True)
            return False
        finally:
            if self.conn:
                self.conn.close()

    def get_user(self, user_id: int):
        """
        Получение информации о пользователе по ID

        Args:
            user_id: ID пользователя Discord

        Returns:
            Словарь с информацией о пользователе или None, если пользователь не найден
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            cursor.execute('''
                SELECT id, display_name, game_static, updated_at 
                FROM users 
                WHERE id = ?
            ''', (user_id,))

            row = cursor.fetchone()

            if row:
                user_info = {
                    'id': row['id'],
                    'display_name': row['display_name'],
                    'game_static': row['game_static'],
                    'updated_at': row['updated_at']
                }
                return user_info

            logger.info(f"Пользователь с ID {user_id} не найден в базе данных")
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении информации о пользователе {user_id}: {e}", exc_info=True)
            return None
        finally:
            if self.conn:
                self.conn.close()

    def get_user_by_game_static(self, game_static: str):
        """
        Получение информации о пользователе по игровому статику

        Args:
            game_static: Игровой статик

        Returns:
            Список словарей с информацией о пользователях с указанным статиком
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            cursor.execute('''
                SELECT id, display_name, game_static, updated_at 
                FROM users 
                WHERE game_static = ?
            ''', (game_static,))

            rows = cursor.fetchall()
            users = []

            for row in rows:
                users.append({
                    'id': row['id'],
                    'display_name': row['display_name'],
                    'game_static': row['game_static'],
                    'updated_at': row['updated_at']
                })

            return users
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении пользователей по статику {game_static}: {e}", exc_info=True)
            return []
        finally:
            if self.conn:
                self.conn.close()

    def get_all_users(self):
        """
        Получение информации о всех пользователях

        Returns:
            Список словарей с информацией о пользователях
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            cursor.execute('SELECT id, display_name, game_static, updated_at FROM users')
            rows = cursor.fetchall()

            users = []
            for row in rows:
                users.append({
                    'id': row['id'],
                    'display_name': row['display_name'],
                    'game_static': row['game_static'],
                    'updated_at': row['updated_at']
                })

            logger.info(f"Получена информация о {len(users)} пользователях")
            return users
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении информации о пользователях: {e}", exc_info=True)
            return []
        finally:
            if self.conn:
                self.conn.close()

    def sync_guild_members(self, guild: discord.Guild):
        """
        Синхронизирует базу данных с текущими пользователями на сервере

        Args:
            guild: Объект сервера Discord

        Returns:
            Кортеж (добавлено, обновлено) с количеством добавленных и обновленных пользователей
        """
        try:
            added = 0
            updated = 0
            
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()
            
            # Получаем существующих пользователей из базы
            cursor.execute('SELECT id FROM users')
            existing_users = {row[0] for row in cursor.fetchall()}
            
            # Добавляем/обновляем пользователей
            for member in guild.members:
                user_id = member.id
                display_name = member.display_name
                game_static = self.extract_game_static(display_name)
                
                if user_id in existing_users:
                    # Обновляем существующего пользователя
                    cursor.execute('''
                        UPDATE users 
                        SET display_name = ?, game_static = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (display_name, game_static, user_id))
                    updated += 1
                else:
                    # Добавляем нового пользователя
                    cursor.execute('''
                        INSERT INTO users (id, display_name, game_static) 
                        VALUES (?, ?, ?)
                    ''', (user_id, display_name, game_static))
                    added += 1
            
            self.conn.commit()
            logger.info(f"Синхронизация пользователей: добавлено {added}, обновлено {updated}")
            return (added, updated)
        except sqlite3.Error as e:
            logger.error(f"Ошибка при синхронизации пользователей: {e}", exc_info=True)
            return (0, 0)
        finally:
            if self.conn:
                self.conn.close()

    def delete_user(self, user_id: int):
        """
        Удаляет пользователя из базы данных

        Args:
            user_id: ID пользователя Discord

        Returns:
            True, если удаление прошло успешно, иначе False
        """
        try:
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()

            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Пользователь с ID {user_id} удален из базы данных")
                return True
            else:
                logger.info(f"Пользователь с ID {user_id} не найден для удаления")
                return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}", exc_info=True)
            return False
        finally:
            if self.conn:
                self.conn.close()

    @classmethod
    def get_instance(cls, db_file="database/user.db"):
        """
        Получение глобального экземпляра менеджера базы данных пользователей

        Args:
            db_file: Путь к файлу базы данных

        Returns:
            Экземпляр менеджера базы данных пользователей
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls(db_file)

        return cls._instance 