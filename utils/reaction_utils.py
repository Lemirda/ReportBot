import os
import uuid
import discord
import datetime
import asyncio

from dotenv import load_dotenv

from utils.logger import Logger
from database.db_manager import DatabaseManager

load_dotenv()

logger = Logger.get_instance()
db_manager = DatabaseManager.get_instance()

LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL', 0))

async def send_log_message(bot, user, content_type, action, message=None, reason=None, author=None):
    """
    Отправка сообщения в лог-канал

    Args:
        bot: Экземпляр бота
        user: Пользователь, отправивший заявку
        content_type: Тип заявки (жалоба/предложение)
        action: Действие (одобрена/отклонена)
        message: Сообщение с эмбедом заявки
        reason: Причина отклонения (опционально)
        author: Модератор, совершивший действие
    """
    if LOG_CHANNEL_ID == 0:
        logger.warning("ID лог-канала не указан в .env файле")
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        logger.warning(f"Лог-канал с ID {LOG_CHANNEL_ID} не найден")
        return

    # Определяем цвет в зависимости от действия
    color = discord.Color.green() if action == "одобрена" else discord.Color.red()

    embed = discord.Embed(
        title=f"{content_type.capitalize()} {action}",
        color=color
    )

    embed.add_field(name="От пользователя", value=f"{user.mention} ({user.name})", inline=False)

    if author:
        embed.add_field(name=f"Кем {action}", value=f"{author.mention} ({author.name})", inline=False)

    # Если есть сообщение с заявкой, добавляем данные из него
    if message and message.embeds:
        original_embed = message.embeds[0]
        for field in original_embed.fields:
            # Не дублируем поле "От кого" и поля статуса
            if field.name not in ["От кого", "Статус", "Причина отклонения"]:
                embed.add_field(name=field.name, value=field.value, inline=field.inline)

    # Если есть причина отклонения, добавляем её
    if reason:
        embed.add_field(name="Причина отклонения", value=reason, inline=False)

    try:
        await channel.send(embed=embed)
        logger.info(f"Отправлено сообщение в лог-канал о {action} {content_type}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в лог-канал: {e}", exc_info=True)

def create_reaction_buttons():
    """
    Создание уникальных ID для кнопок реакции

    Returns:
        Кортеж из двух ID (approve_id, reject_id)
    """
    approve_id = f"approve_{str(uuid.uuid4())[:8]}"
    reject_id = f"reject_{str(uuid.uuid4())[:8]}"
    return approve_id, reject_id

class ReactionView(discord.ui.View):
    """Представление с кнопками для реакции на заявку"""

    def __init__(self, bot, user, content_type, message_id=None, channel_id=None):
        """
        Инициализация представления с кнопками

        Args:
            bot: Экземпляр бота
            user: Пользователь, отправивший заявку
            content_type: Тип заявки (жалоба/предложение)
            message_id: ID сообщения (для загрузки из БД)
            channel_id: ID канала (для загрузки из БД)
        """
        super().__init__(timeout=None)

        self.bot = bot
        self.user = user
        self.content_type = content_type

        # Генерируем ID для кнопок или загружаем из базы
        if message_id and channel_id:
            # Загружаем данные для существующей кнопки
            buttons = db_manager.get_reaction_buttons(message_id, channel_id)

            if buttons:
                self.approve_id = buttons.get('approve_button_id')
                self.reject_id = buttons.get('reject_button_id')
            else:
                # Если данные не найдены, генерируем новые ID
                self.approve_id, self.reject_id = create_reaction_buttons()
        else:
            # Генерируем новые ID для новых кнопок
            self.approve_id, self.reject_id = create_reaction_buttons()

        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Одобрить",
            custom_id=self.approve_id
        ))

        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Отклонить",
            custom_id=self.reject_id
        ))

class RejectionModal(discord.ui.Modal, title="Отклонение заявки"):
    """
    Модальное окно для ввода причины отклонения заявки

    Attributes:
        bot: Экземпляр бота
        message: Сообщение с кнопками
        user: Пользователь, создавший заявку
    """
    reason = discord.ui.TextInput(
        label="Причина отклонения",
        placeholder="Укажите причину отклонения заявки...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, bot, message, user):
        super().__init__()
        self.bot = bot
        self.message = message
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        channel = self.message.channel
        content_type = "жалоба" if "жалоба" in channel.name else "предложение"

        current_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        db_manager.log_reaction_action(
            self.message.id,
            channel.id,
            self.user.id,
            interaction.user.id,
            "reject",
            self.reason.value
        )

        await send_log_message(
            bot=self.bot,
            user=self.user,
            content_type=content_type,
            action="отклонена",
            message=self.message,
            reason=self.reason.value,
            author=interaction.user
        )

        await interaction.response.send_message(
            f"Вы отклонили {content_type} от {self.user.mention} по причине: {self.reason.value}. Канал будет удален через 10 секунд.", 
            ephemeral=True
        )

        try:
            embed = discord.Embed(
                title=f"{content_type.capitalize()} отклонена", 
                description=f"Ваша {content_type} была отклонена модератором {interaction.user.mention}.", 
                color=discord.Color.red()
            )

            if self.message.embeds:
                original_embed = self.message.embeds[0]
                for field in original_embed.fields:
                    # Не дублируем поле "От кого" и поля статуса
                    if field.name not in ["От кого", "Статус", "Причина отклонения"]:
                        embed.add_field(name=field.name, value=field.value, inline=field.inline)

            embed.add_field(name="Причина отклонения", value=self.reason.value, inline=False)

            embed.set_footer(text=f"{current_date}")

            await self.user.send(embed=embed)
            logger.info(f"Отправлено уведомление пользователю {self.user.name} об отклонении {content_type}")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {self.user.name}: {e}")

        # Обновляем сообщение, чтобы отключить кнопки
        for item in self.message.components:
            for child in item.children:
                child.disabled = True

        embed = self.message.embeds[0]

        for i, field in enumerate(embed.fields):
            if field.name == "Статус":
                embed.set_field_at(i, name="Статус", value="Отклонена", inline=False)
                break
        else:

            embed.add_field(name="Статус", value="Отклонена", inline=False)

        embed.add_field(name="Причина отклонения", value=self.reason.value, inline=False)

        await self.message.edit(embed=embed, view=None)

        await asyncio.sleep(10)

        try:
            await channel.delete(reason=f"{content_type.capitalize()} отклонена модератором {interaction.user.name}")
            logger.info(f"Канал {channel.name} удален после отклонения {content_type}")
        except Exception as e:
            logger.error(f"Ошибка при удалении канала {channel.name}: {e}", exc_info=True)
            # Если не удалось удалить канал, отправляем сообщение
            try:
                await channel.send(f"Не удалось автоматически удалить канал. Пожалуйста, удалите его вручную.")
            except:
                pass

async def handle_reaction_button(bot, interaction):
    """
    Обработка нажатия на кнопку реакции

    Args:
        bot: Экземпляр бота
        interaction: Объект взаимодействия
    """
    button_id = interaction.data.get('custom_id')

    button_info = db_manager.get_button_info_by_id(button_id)

    if not button_info:
        logger.warning(f"Кнопка с ID {button_id} не найдена в базе данных")
        await interaction.response.send_message(
            "Эта кнопка больше не действительна.", 
            ephemeral=True
        )
        return

    channel = bot.get_channel(int(button_info['channel_id']))

    if not channel:
        logger.warning(f"Канал с ID {button_info['channel_id']} не найден")
        await interaction.response.send_message(
            "Канал для этой заявки не найден.", 
            ephemeral=True
        )
        return

    try:
        message = await channel.fetch_message(int(button_info['message_id']))
    except discord.NotFound:
        logger.warning(f"Сообщение с ID {button_info['message_id']} не найдено")
        await interaction.response.send_message(
            "Сообщение с заявкой не найдено.", 
            ephemeral=True
        )
        return

    user_id = None
    user = None
    content_type = button_info['type']

    if message.embeds:
        embed = message.embeds[0]
        # Ищем поле "От кого"
        for field in embed.fields:
            if field.name == "От кого":
                # Извлекаем ID пользователя из упоминания
                if field.value and "<@" in field.value:
                    user_id = field.value.split("<@")[1].split(">")[0]
                    try:
                        user = await bot.fetch_user(int(user_id))
                    except:
                        logger.warning(f"Не удалось получить пользователя с ID {user_id}")
                break

    if not user:
        logger.warning("Не удалось определить пользователя из эмбеда")
        user = interaction.user

    if button_info['is_approve']:
        # Кнопка одобрения
        await handle_approve(bot, interaction, message, user)
    else:
        # Кнопка отклонения
        await handle_reject(bot, interaction, message, user)

async def handle_approve(bot, interaction, message, user):
    """
    Обработка нажатия кнопки одобрения

    Args:
        bot: Экземпляр бота
        interaction: Объект взаимодействия
        message: Сообщение с кнопками
        user: Пользователь, создавший заявку
    """
    channel = message.channel
    content_type = "жалоба" if "жалоба" in channel.name else "предложение"

    current_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    db_manager.log_reaction_action(
        message.id,
        channel.id,
        user.id,
        interaction.user.id,
        "approve"
    )

    await send_log_message(
        bot=bot,
        user=user,
        content_type=content_type,
        action="одобрена",
        message=message,
        author=interaction.user
    )

    await interaction.response.send_message(f"Вы одобрили {content_type} от {user.mention}. Канал будет удален через 10 секунд.", ephemeral=True)

    try:
        embed = discord.Embed(
            title=f"{content_type.capitalize()} одобрена", 
            description=f"Ваша {content_type} была одобрена модератором {interaction.user.mention}.", 
            color=discord.Color.green()
        )

        if message.embeds:
            original_embed = message.embeds[0]
            for field in original_embed.fields:
                # Не дублируем поле "От кого" и поля статуса
                if field.name not in ["От кого", "Статус", "Причина отклонения"]:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)

        embed.set_footer(text=f"{current_date}")

        await user.send(embed=embed)
        logger.info(f"Отправлено уведомление пользователю {user.name} об одобрении {content_type}")
    except Exception as e:
        logger.warning(f"Не удалось отправить сообщение пользователю {user.name}: {e}")

    for item in message.components:
        for child in item.children:
            child.disabled = True

    embed = message.embeds[0]
    # Обновляем статус в эмбеде
    for i, field in enumerate(embed.fields):
        if field.name == "Статус":
            embed.set_field_at(i, name="Статус", value="Одобрена", inline=False)
            break
    else:
        # Если поле статуса не найдено, добавляем его
        embed.add_field(name="Статус", value="Одобрена", inline=False)

    await message.edit(embed=embed, view=None)

    await asyncio.sleep(10)

    try:
        await channel.delete(reason=f"{content_type.capitalize()} одобрена модератором {interaction.user.name}")
        logger.info(f"Канал {channel.name} удален после одобрения {content_type}")
    except Exception as e:
        logger.error(f"Ошибка при удалении канала {channel.name}: {e}", exc_info=True)
        # Если не удалось удалить канал, отправляем сообщение
        try:
            await channel.send(f"Не удалось автоматически удалить канал. Пожалуйста, удалите его вручную.")
        except:
            pass

async def handle_reject(bot, interaction, message, user):
    """
    Обработка нажатия кнопки отклонения

    Args:
        bot: Экземпляр бота
        interaction: Объект взаимодействия
        message: Сообщение с кнопками
        user: Пользователь, создавший заявку
    """
    # Отправляем модальное окно для ввода причины отклонения
    await interaction.response.send_modal(
        RejectionModal(bot, message, user)
    )