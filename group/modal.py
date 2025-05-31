import discord
from discord import ui
import re
import os
import uuid
from datetime import datetime, timezone, timedelta

from tools.logger import Logger
from database.group import GroupDatabase

logger = Logger.get_instance()

# Получаем ID роли Rave из переменных окружения
RAVE_ROLE_ID = int(os.getenv('RAVE_ROLE', 0))

class GroupTimeModal(ui.Modal, title="Время группы"):
    """Модальное окно для ввода времени группы"""
    
    time = ui.TextInput(
        label="Время (формат: ЧЧ:ММ)",
        placeholder="Например: 15:30",
        required=True,
        min_length=5,
        max_length=5
    )
    
    def __init__(self, group_type):
        super().__init__()
        self.group_type = group_type
        
    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            # Проверяем формат времени
            time_str = self.time.value
            if not re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', time_str):
                await interaction.response.send_message(
                    "Неверный формат времени. Используйте формат ЧЧ:ММ (например: 15:30)",
                    ephemeral=True
                )
                return
            
            # Получаем текущее время в МСК
            moscow_tz = timezone(timedelta(hours=3))
            current_time = datetime.now(moscow_tz)
            
            # Отправляем сообщения в канал
            await interaction.response.defer(ephemeral=True)
            
            # Формируем сообщение с упоминанием роли
            role_mention = f"<@&{RAVE_ROLE_ID}>"
            
            # Генерируем уникальный ID для группы сообщений
            group_id = str(uuid.uuid4())
            
            # Получаем экземпляр базы данных
            db = GroupDatabase.get_instance()
            
            # Создаем 5 сообщений для группы
            for _ in range(5):
                message = await interaction.channel.send(f"{role_mention} Групп {self.group_type} {time_str}")
                # Сохраняем сообщение в базу данных
                db.save_message(
                    group_id=group_id,
                    message_id=message.id,
                    channel_id=interaction.channel_id,
                    message_type=self.group_type,
                    creator_id=interaction.user.id,
                    minutes_to_delete=5
                )
            
            # Отправляем подтверждение пользователю
            await interaction.followup.send(
                f"Группа {self.group_type} на {time_str} успешно создана! Сообщения будут автоматически удалены через 5 минут.",
                ephemeral=True
            )
            
            # Логируем событие
            from group.manager import GroupManager
            group_manager = GroupManager.get_instance()
            await group_manager.log_group_creation(
                interaction.user,
                self.group_type,
                time_str
            )
            
            logger.info(f"Пользователь {interaction.user.display_name} создал группу {self.group_type} на {time_str}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании группы: {e}", exc_info=True)
            await interaction.followup.send(
                "Произошла ошибка при создании группы. Пожалуйста, попробуйте позже.",
                ephemeral=True
            )


class CustomGroupModal(ui.Modal, title="Создание собственного МП"):
    """Модальное окно для создания собственного МП"""
    
    name = ui.TextInput(
        label="Название МП",
        placeholder="Введите название мероприятия",
        required=True,
        min_length=1,
        max_length=100
    )
    
    time = ui.TextInput(
        label="Время (формат: ЧЧ:ММ)",
        placeholder="Например: 15:30",
        required=True,
        min_length=5,
        max_length=5
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            # Проверяем формат времени
            time_str = self.time.value
            if not re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', time_str):
                await interaction.response.send_message(
                    "Неверный формат времени. Используйте формат ЧЧ:ММ (например: 15:30)",
                    ephemeral=True
                )
                return
            
            # Получаем название МП
            mp_name = self.name.value
            
            # Отправляем сообщения в канал
            await interaction.response.defer(ephemeral=True)
            
            # Формируем сообщение с упоминанием роли
            role_mention = f"<@&{RAVE_ROLE_ID}>"
            
            # Генерируем уникальный ID для группы сообщений
            group_id = str(uuid.uuid4())
            
            # Получаем экземпляр базы данных
            db = GroupDatabase.get_instance()
            
            # Создаем 5 сообщений для группы
            for _ in range(5):
                message = await interaction.channel.send(f"{role_mention} {mp_name} {time_str}")
                # Сохраняем сообщение в базу данных
                db.save_message(
                    group_id=group_id,
                    message_id=message.id,
                    channel_id=interaction.channel_id,
                    message_type=mp_name,
                    creator_id=interaction.user.id,
                    minutes_to_delete=5
                )
            
            # Отправляем подтверждение пользователю
            await interaction.followup.send(
                f"Мероприятие '{mp_name}' на {time_str} успешно создано! Сообщения будут автоматически удалены через 5 минут.",
                ephemeral=True
            )
            
            # Логируем событие
            from group.manager import GroupManager
            group_manager = GroupManager.get_instance()
            await group_manager.log_group_creation(
                interaction.user,
                mp_name,
                time_str
            )
            
            logger.info(f"Пользователь {interaction.user.display_name} создал мероприятие '{mp_name}' на {time_str}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании мероприятия: {e}", exc_info=True)
            await interaction.followup.send(
                "Произошла ошибка при создании мероприятия. Пожалуйста, попробуйте позже.",
                ephemeral=True
            ) 