import discord
from discord.ext import tasks
from datetime import datetime as dt

from tools.logger import Logger
from capt.view import CaptView

logger = Logger.get_instance()

class CaptScheduler:
    """Планировщик для автоматического закрытия просроченных сборов"""
    
    def __init__(self, bot, capt_db):
        self.bot = bot
        self.capt_db = capt_db
        self.active_capts = {}
        
        # Запускаем фоновую задачу для проверки устаревших сборов
        self.check_outdated_capts.start()
        
    def set_active_capts(self, active_capts):
        """Устанавливает словарь активных сборов из CaptCommand"""
        self.active_capts = active_capts
        
    def cog_unload(self):
        """Останавливаем фоновую задачу при выгрузке модуля"""
        self.check_outdated_capts.cancel()
        
    @tasks.loop(minutes=5)  # Проверяем каждые 5 минут
    async def check_outdated_capts(self):
        """Фоновая задача для проверки и закрытия сборов с истекшим временем"""
        try:
            await self.close_outdated_capts()
        except Exception as e:
            logger.error(f"Ошибка при проверке устаревших сборов: {e}", exc_info=True)
            
    @check_outdated_capts.before_loop
    async def before_check_outdated_capts(self):
        """Ждем, пока бот полностью загрузится"""
        await self.bot.wait_until_ready()
            
    async def close_outdated_capts(self):
        """Закрывает все сборы, у которых истекло время"""
        if not self.active_capts:
            return
            
        current_time = dt.now()
        capts_to_close = []
        
        # Проверяем все активные сборы
        for message_id, capt_data in self.active_capts.items():
            try:
                # Парсим дату и время сбора
                capt_time = dt.strptime(capt_data['datetime'], "%d.%m.%Y %H:%M")
                
                # Если время сбора прошло, добавляем его в список для закрытия
                if current_time > capt_time:
                    capts_to_close.append((message_id, capt_data))
            except Exception as e:
                logger.error(f"Ошибка при проверке времени сбора {message_id}: {e}", exc_info=True)
        
        # Закрываем просроченные сборы
        for message_id, capt_data in capts_to_close:
            try:
                # Получаем канал и сообщение
                channel_id = capt_data['channel_id']
                channel = self.bot.get_channel(int(channel_id))
                
                if not channel:
                    logger.warning(f"Канал {channel_id} не найден для сбора {capt_data['name']}")
                    continue
                    
                try:
                    message = await channel.fetch_message(int(message_id))
                except discord.NotFound:
                    logger.warning(f"Сообщение {message_id} не найдено для сбора {capt_data['name']}")
                    self.capt_db.delete_capt(message_id)
                    if message_id in self.active_capts:
                        del self.active_capts[message_id]
                    continue
                
                # Отправляем сообщение о закрытии в тред, если он существует
                if 'thread_id' in capt_data and capt_data['thread_id']:
                    try:
                        thread_id = capt_data['thread_id']
                        thread = channel.get_thread(thread_id)
                        if thread:
                            await thread.send(f"**Сбор автоматически закрыт**, так как время сбора ({capt_data['datetime']}) уже прошло.")
                    except Exception as thread_error:
                        logger.error(f"Ошибка при отправке сообщения в тред для сбора {message_id}: {thread_error}", exc_info=True)
                
                # Получаем view из сообщения, если возможно
                if message.components:
                    # Создаем новое view с деактивированными кнопками
                    view = CaptView(capt_data)
                    view.update_button_ids(message_id)
                    
                    # Деактивируем все кнопки
                    for child in view.children:
                        child.disabled = True
                    
                    # Обновляем сообщение с деактивированными кнопками
                    await message.edit(view=view)
                
                # Удаляем сбор из базы данных и из памяти
                self.capt_db.delete_capt(message_id)
                if message_id in self.active_capts:
                    del self.active_capts[message_id]
                    
                logger.info(f"Автоматически закрыт просроченный сбор '{capt_data['name']}' (ID: {message_id}, время: {capt_data['datetime']})")
                
            except Exception as e:
                logger.error(f"Ошибка при закрытии просроченного сбора {message_id}: {e}", exc_info=True)