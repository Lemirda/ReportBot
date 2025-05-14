import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime as dt
import re
import os
import asyncio

from tools.logger import Logger
from tools.embed import EmbedBuilder
from capt.view import CaptView
from database.capt import get_instance as get_capt_db
from capt.ranks import RAVE_ROLE_ID, can_manage_capt

logger = Logger.get_instance()

class CaptCommand(commands.Cog):
    """Команда для создания сбора игроков"""
    
    def __init__(self, bot):
        self.bot = bot
        self.capt_db = get_capt_db()
        # Словарь для хранения данных сборов в памяти (ключ - ID сообщения)
        self.active_capts = {}
        
    @app_commands.command(name="capt", description="Создать сбор игроков")
    @app_commands.describe(
        name="Название сбора",
        date_time="Дата и время проведения (формат: DD.MM.YYYY HH:MM, например: 20.05.2025 20:00)",
        slots="Количество слотов (минимум 1)"
    )
    async def capt(self, interaction: discord.Interaction, name: str, date_time: str, slots: int):
        try:
            # Проверяем, есть ли у пользователя права на создание сбора
            if not can_manage_capt(interaction.user):
                await interaction.response.send_message("У вас нет прав на создание сборов", ephemeral=True)
                return
                
            # Проверка корректности параметров
            if not name or len(name) > 100:
                await interaction.response.send_message("Название сбора должно быть от 1 до 100 символов", ephemeral=True)
                return
                
            if slots < 1:
                await interaction.response.send_message("Количество слотов должно быть не менее 1", ephemeral=True)
                return
            
            # Проверка формата даты и времени
            date_pattern = r'^(\d{2})\.(\d{2})\.(\d{4})\s(\d{2}):(\d{2})$'
            match = re.match(date_pattern, date_time)
            
            if not match:
                await interaction.response.send_message(
                    "Неверный формат даты и времени. Используйте формат: DD.MM.YYYY HH:MM (например: 20.05.2023 20:00)",
                    ephemeral=True
                )
                return
            
            # Проверка валидности даты (существующие день, месяц и т.д.)
            try:
                day, month, year, hour, minute = map(int, match.groups())
                
                # Проверка диапазонов
                if not (1 <= day <= 31):
                    await interaction.response.send_message("День должен быть от 1 до 31", ephemeral=True)
                    return
                    
                if not (1 <= month <= 12):
                    await interaction.response.send_message("Месяц должен быть от 1 до 12", ephemeral=True)
                    return
                    
                if not (0 <= hour <= 23):
                    await interaction.response.send_message("Час должен быть от 0 до 23", ephemeral=True)
                    return
                    
                if not (0 <= minute <= 59):
                    await interaction.response.send_message("Минута должна быть от 0 до 59", ephemeral=True)
                    return
                
                # Проверка валидности даты через создание объекта datetime
                parsed_date = dt(year, month, day, hour, minute)
                
            except ValueError:
                await interaction.response.send_message(
                    "Указана некорректная дата. Пожалуйста, проверьте дату и время.",
                    ephemeral=True
                )
                return
            
            # Создаем данные для сбора
            capt_data = {
                'name': name,
                'creator': interaction.user,
                'datetime': date_time,
                'slots': slots,
                'participants': [],
                'extra_participants': [],
                'guild_id': interaction.guild.id,
                'channel_id': interaction.channel.id
            }
            
            # Создаем эмбед
            embed = EmbedBuilder.create_capt_embed(capt_data)
            
            # Создаем view с упрощенными ID кнопок (будут обновлены после отправки)
            view = CaptView(capt_data)
            
            # Создаем строку для пинга роли Rave, если она настроена
            content = None
            if RAVE_ROLE_ID != 0:
                content = f"<@&{RAVE_ROLE_ID}>"
            
            # Отправляем сообщение с контентом для пинга и эмбедом
            await interaction.response.send_message(content=content, embed=embed, view=view)
            
            # Получаем отправленное сообщение
            sent_message = await interaction.original_response()
            message_id = str(sent_message.id)
            
            # Обновляем ID кнопок, чтобы они включали ID сообщения
            view.update_button_ids(message_id)
            await sent_message.edit(view=view)
            
            # Сохраняем view в боте для персистентности
            self.bot.add_view(view)
            
            # Сохраняем данные сбора в словаре для быстрого доступа в памяти
            self.active_capts[message_id] = capt_data
            
            # Сохраняем данные в базу данных
            self.capt_db.save_capt(message_id, capt_data)
            
            logger.info(f"Пользователь {interaction.user.name} создал сбор '{name}' на {date_time} с {slots} слотами. ID сообщения: {message_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании сбора: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка при создании сбора. Пожалуйста, попробуйте позже.", ephemeral=True)
    
    async def sync_views(self):
        """Восстанавливает работу кнопок в существующих сборах при запуске бота"""
        try:
            # Чистим старые сборы (старше 7 дней)
            self.capt_db.clean_old_capts(7)
            
            # Загружаем данные из базы данных
            saved_capts = self.capt_db.get_all_capts()
            if not saved_capts:
                logger.info("Нет сохраненных сборов для восстановления")
                return
            
            logger.info(f"Начинаю восстановление {len(saved_capts)} сборов...")
            
            for message_id, capt_info in saved_capts.items():
                try:
                    # Получаем гильдию и канал
                    guild = self.bot.get_guild(int(capt_info["guild_id"]))
                    if not guild:
                        logger.warning(f"Гильдия {capt_info['guild_id']} не найдена для сбора {capt_info['name']}")
                        continue
                    
                    channel = guild.get_channel(int(capt_info["channel_id"]))
                    if not channel:
                        logger.warning(f"Канал {capt_info['channel_id']} не найден для сбора {capt_info['name']}")
                        continue
                    
                    # Пытаемся получить сообщение
                    try:
                        message = await channel.fetch_message(int(message_id))
                    except discord.NotFound:
                        logger.warning(f"Сообщение {message_id} не найдено для сбора {capt_info['name']}")
                        # Удаляем сбор из базы, так как сообщение больше не существует
                        self.capt_db.delete_capt(message_id)
                        continue
                    
                    # Находим создателя
                    creator = guild.get_member(int(capt_info["creator"]["id"]))
                    if not creator:
                        # Если создатель не найден, используем бота
                        creator = self.bot.user
                    
                    # Восстанавливаем данные сбора
                    capt_data = {
                        'name': capt_info["name"],
                        'creator': creator,
                        'datetime': capt_info["datetime"],
                        'slots': capt_info["slots"],
                        'participants': [],
                        'extra_participants': [],
                        'guild_id': capt_info["guild_id"],
                        'channel_id': capt_info["channel_id"]
                    }
                    
                    # Восстанавливаем списки участников
                    for participant_info in capt_info["participants"]:
                        user = guild.get_member(int(participant_info["id"]))
                        if user:
                            capt_data['participants'].append(user)
                    
                    for participant_info in capt_info["extra_participants"]:
                        user = guild.get_member(int(participant_info["id"]))
                        if user:
                            capt_data['extra_participants'].append(user)
                    
                    # Создаем новое представление с восстановленными данными
                    view = CaptView(capt_data)
                    view.update_button_ids(message_id)
                    
                    # Регистрируем представление
                    self.bot.add_view(view)
                    
                    # Сохраняем в нашем словаре
                    self.active_capts[message_id] = capt_data
                    
                    logger.info(f"Восстановлен сбор '{capt_info['name']}' в канале {channel.name}")
                
                except Exception as capt_error:
                    logger.error(f"Ошибка при восстановлении сбора с ID {message_id}: {capt_error}", exc_info=True)
            
            logger.info(f"Восстановление сборов завершено. Активно {len(self.active_capts)} сборов.")
        
        except Exception as e:
            logger.error(f"Ошибка при синхронизации сборов: {e}", exc_info=True)
    
    # Метод для обновления данных сбора
    def update_capt_data(self, message_id, capt_data):
        """Обновляет данные сбора и сохраняет в базе"""
        if message_id in self.active_capts:
            self.active_capts[message_id] = capt_data
            self.capt_db.save_capt(message_id, capt_data)
    
    # Метод для удаления сбора
    def remove_capt(self, message_id):
        """Удаляет сбор из активных сборов"""
        if message_id in self.active_capts:
            del self.active_capts[message_id]
            self.capt_db.delete_capt(message_id)
            logger.info(f"Сбор с ID {message_id} удален из активных")

async def setup(bot):
    cog = CaptCommand(bot)
    await bot.add_cog(cog)
    # Запускаем синхронизацию существующих сборов
    await cog.sync_views() 