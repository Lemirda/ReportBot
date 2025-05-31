import os
import discord
from discord.ext import tasks
from datetime import datetime, timezone, timedelta
import asyncio

from tools.logger import Logger
from database.group import GroupDatabase

logger = Logger.get_instance()

class GroupManager:
    """Менеджер для управления группами"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Получение единственного экземпляра класса (Singleton)"""
        if cls._instance is None:
            cls._instance = GroupManager()
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера групп"""
        self.bot = None
        self.group_channel_id = None
        self.log_channel_id = None
        
        # Загружаем ID каналов из переменных окружения
        self.load_env_vars()
        
    def load_env_vars(self):
        """Загрузка переменных окружения"""
        try:
            self.group_channel_id = int(os.getenv('GROUP_CHANNEL_ID', 0))
            self.log_channel_id = int(os.getenv('GROUP_LOG_CHANNEL_ID', 0))
            
            if self.group_channel_id == 0 or self.log_channel_id == 0:
                logger.warning("ID каналов для групп не настроены в .env")
        except Exception as e:
            logger.error(f"Ошибка при загрузке ID каналов для групп: {e}", exc_info=True)
    
    def setup(self, bot):
        """Настройка менеджера с ботом"""
        self.bot = bot
        
        # Запускаем задачи по расписанию
        self.check_messages_to_delete.start()
        
        logger.info("Менеджер групп успешно инициализирован")
    
    def cog_unload(self):
        """Остановка задач при выгрузке модуля"""
        self.check_messages_to_delete.cancel()
    
    async def log_group_creation(self, user, group_type, time):
        """Логирование создания группы в лог-канал"""
        try:
            if not self.bot or self.log_channel_id == 0:
                logger.warning("Невозможно залогировать создание группы: бот не инициализирован или ID лог-канала не настроен")
                return
            
            log_channel = self.bot.get_channel(self.log_channel_id)
            if not log_channel:
                logger.warning(f"Лог-канал с ID {self.log_channel_id} не найден")
                return
            
            # Отправляем сообщение в лог-канал
            await log_channel.send(f"{user.display_name} запустил групп на {group_type} в {time}")
            
        except Exception as e:
            logger.error(f"Ошибка при логировании создания группы: {e}", exc_info=True)
    
    @tasks.loop(seconds=30)
    async def check_messages_to_delete(self):
        """Проверяет сообщения, которые нужно удалить"""
        try:
            if not self.bot:
                return
            
            # Получаем сообщения для удаления из базы данных
            db = GroupDatabase.get_instance()
            messages_to_delete = db.get_messages_to_delete()
            
            if not messages_to_delete:
                return
            
            logger.info(f"Найдено {len(messages_to_delete)} сообщений для удаления")
            
            for group_id, message_id, channel_id in messages_to_delete:
                try:
                    # Преобразуем ID канала и сообщения в int
                    channel_id_int = int(channel_id)
                    message_id_int = int(message_id)
                    
                    # Получаем канал
                    channel = self.bot.get_channel(channel_id_int)
                    if not channel:
                        logger.warning(f"Канал с ID {channel_id} не найден, удаляем запись из БД")
                        db.delete_message_record(message_id)
                        continue
                    
                    # Получаем сообщение
                    try:
                        message = await channel.fetch_message(message_id_int)
                        # Удаляем сообщение
                        await message.delete()
                        logger.info(f"Сообщение с ID {message_id} успешно удалено")
                    except discord.NotFound:
                        logger.warning(f"Сообщение с ID {message_id} не найдено, удаляем запись из БД")
                    except discord.Forbidden:
                        logger.warning(f"Недостаточно прав для удаления сообщения с ID {message_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении сообщения с ID {message_id}: {e}", exc_info=True)
                    
                    # Удаляем запись из базы данных
                    db.delete_message_record(message_id)
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения {message_id}: {e}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Ошибка при проверке сообщений для удаления: {e}", exc_info=True)