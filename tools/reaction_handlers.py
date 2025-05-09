import os
import uuid
import discord
import re

from dotenv import load_dotenv

from tools.logger import Logger
from database.db_manager import DatabaseManager
from tools.notification_manager import NotificationManager
from tools.log_manager import LogManager
from tools.embed import EmbedBuilder

load_dotenv()

logger = Logger.get_instance()
db_manager = DatabaseManager.get_instance()

REPORT_LOG_CHANNEL=int(os.getenv('REPORT_LOG_CHANNEL'))
ORDER_LOG_CHANNEL=int(os.getenv('ORDER_LOG_CHANNEL'))

def create_reaction_buttons():
    """Создание уникальных ID для кнопок реакции"""
    approve_id = f"approve_{str(uuid.uuid4())[:8]}"
    reject_id = f"reject_{str(uuid.uuid4())[:8]}"
    return approve_id, reject_id

class ReactionView(discord.ui.View):
    """Представление с кнопками для реакции на заявку"""
    
    def __init__(self, message, user):
        super().__init__(timeout=None)
        self.message = message
        self.user = user
        
        approve_id, reject_id = create_reaction_buttons()
        
        approve_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Одобрить",
            emoji="✅",
            custom_id=approve_id
        )
        
        reject_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Отклонить",
            emoji="❌",
            custom_id=reject_id
        )
        
        self.add_item(approve_button)
        self.add_item(reject_button)

class RejectReasonModal(discord.ui.Modal, title="Причина отклонения"):
    """Модальное окно для ввода причины отклонения заявки"""
    
    reason = discord.ui.TextInput(
        label="Причина отклонения",
        placeholder="Укажите причину отклонения...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    def __init__(self, message, user):
        super().__init__()
        self.message = message
        self.user = user
    
    async def on_submit(self, interaction: discord.Interaction):
        channel = self.message.channel
        
        # Определяем тип содержимого канала на основе его имени
        channel_name = channel.name.lower()
        if "жалоба" in channel_name:
            content_type = "жалоба"
            status = "отклонена"
        elif "предложение" in channel_name:
            content_type = "предложение"
            status = "отклонено"
        elif "запрос" in channel_name:
            content_type = "запрос"
            status = "отклонен"
        elif "повышение" in channel_name:
            content_type = "повышение"
            status = "отклонено"
        else:
            content_type = "заявка"
            status = "отклонена"
        
        # Создаем эмбед для уведомления пользователя
        embed = EmbedBuilder.create_decision_embed(
            content_type=content_type,
            is_approved=False,
            moderator=interaction.user,
            original_embed=self.message.embeds[0] if self.message.embeds else None,
            reason=self.reason.value
        )

        # Отправляем уведомление пользователю
        await NotificationManager.send_decision_notification(
            self.user, 
            embed
        )

        # Отправляем сообщение в лог-канал, если это жалоба или запрос
        try:
            if content_type == "жалоба" and REPORT_LOG_CHANNEL:
                log_channel = interaction.guild.get_channel(REPORT_LOG_CHANNEL)
                if log_channel:
                    await LogManager.send_decision_log(
                        channel=log_channel,
                        content_type=content_type,
                        status=status,
                        color=discord.Color.red(),
                        user=self.user,
                        moderator=interaction.user,
                        reason=self.reason.value,
                        original_embed=self.message.embeds[0] if self.message.embeds else None
                    )
            elif content_type == "запрос" and ORDER_LOG_CHANNEL:
                log_channel = interaction.guild.get_channel(ORDER_LOG_CHANNEL)
                if log_channel:
                    await LogManager.send_decision_log(
                        channel=log_channel,
                        content_type=content_type,
                        status=status,
                        color=discord.Color.red(),
                        user=self.user,
                        moderator=interaction.user,
                        reason=self.reason.value,
                        original_embed=self.message.embeds[0] if self.message.embeds else None
                    )
            elif content_type == "повышение" and os.getenv('PROMOTION_LOG_CHANNEL'):
                promotion_log_channel_id = int(os.getenv('PROMOTION_LOG_CHANNEL'))
                log_channel = interaction.guild.get_channel(promotion_log_channel_id)
                if log_channel:
                    await LogManager.send_decision_log(
                        channel=log_channel,
                        content_type=content_type,
                        status=status,
                        color=discord.Color.red(),
                        user=self.user,
                        moderator=interaction.user,
                        reason=self.reason.value,
                        original_embed=self.message.embeds[0] if self.message.embeds else None
                    )
        except Exception as e:
            logger.error(f"Ошибка при отправке лога решения: {e}", exc_info=True)

        # Используем defer() вместо отправки сообщения
        await interaction.response.defer()

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

async def handle_approve(bot, interaction, message, user):
    """
    Обработка нажатия на кнопку "Одобрить"
    
    Args:
        bot: Бот Discord
        interaction: Объект взаимодействия
        message: Сообщение с кнопками
        user: Пользователь, оставивший заявку
        
    Returns:
        None
    """
    channel = message.channel
    
    # Определяем тип содержимого на основе имени канала
    channel_name = channel.name.lower()
    if "жалоба" in channel_name:
        content_type = "жалоба"
        status = "одобрена"
    elif "предложение" in channel_name:
        content_type = "предложение"
        status = "одобрено"
    elif "запрос" in channel_name:
        content_type = "запрос"
        status = "одобрен"
    elif "повышение" in channel_name:
        content_type = "повышение"
        status = "одобрено"
    else:
        content_type = "заявка"
        status = "одобрена"
    
    # Если это запрос, пытаемся получить ID заказа
    order_id = None
    if content_type == "запрос" and message.embeds:
        # Ищем ID заказа в футере первого эмбеда
        footer_text = message.embeds[0].footer.text
        id_match = re.search(r'ID заказа: (ORD-\d+-\d+)', footer_text)
        if id_match:
            order_id = id_match.group(1)
    
    # Если это заказ, получаем информацию о цене
    order_price = None
    if content_type == "запрос" and message.embeds:
        # Ищем информацию о цене в полях эмбеда
        for field in message.embeds[0].fields:
            if field.name == "💰 Информация":
                price_match = re.search(r'Стоимость: ([\d.,\- +]+)', field.value)
                if price_match:
                    order_price = price_match.group(1)
                break
                
    # Если это повышение, выдаем роль следующего ранга
    if content_type == "повышение" and message.embeds:
        try:
            next_rank = None
            # Получаем информацию о повышении из первого поля эмбеда
            if message.embeds[0].fields:
                user_field = message.embeds[0].fields[0]
                if user_field.name == "👤 Пользователь":
                    rank_match = re.search(r'с (\d+) ранга на (\d+) ранг', user_field.value)
                    if rank_match:
                        current_rank = int(rank_match.group(1))
                        next_rank = int(rank_match.group(2))
                        
            if next_rank:
                # Получаем ID роли для нового ранга
                rank_role_id = int(os.getenv(f'RANK_{next_rank}', 0))
                
                if rank_role_id:
                    # Получаем объект роли
                    rank_role = interaction.guild.get_role(rank_role_id)
                    
                    if rank_role:
                        # Находим участника на сервере
                        member = interaction.guild.get_member(user.id)
                        
                        if member:
                            # Выдаем роль
                            await member.add_roles(rank_role)
                            logger.info(f"Роль {rank_role.name} успешно выдана пользователю {user.name} при повышении с {current_rank} до {next_rank} ранга")
                            
                            # Удаляем предыдущую роль ранга, если она есть
                            if current_rank > 0:
                                prev_rank_role_id = int(os.getenv(f'RANK_{current_rank}', 0))
                                if prev_rank_role_id:
                                    prev_rank_role = interaction.guild.get_role(prev_rank_role_id)
                                    if prev_rank_role and prev_rank_role in member.roles:
                                        await member.remove_roles(prev_rank_role)
                                        logger.info(f"Роль {prev_rank_role.name} успешно удалена у пользователя {user.name} при повышении")
                        else:
                            logger.warning(f"Не удалось найти участника {user.name} на сервере для выдачи роли")
                    else:
                        logger.warning(f"Не удалось найти роль с ID {rank_role_id} для ранга {next_rank}")
                else:
                    logger.warning(f"ID роли для ранга {next_rank} не найден в переменных окружения")
        except Exception as e:
            logger.error(f"Ошибка при выдаче роли для повышения: {e}", exc_info=True)

    # Создаем эмбед для уведомления пользователя
    embed = EmbedBuilder.create_decision_embed(
        content_type=content_type,
        is_approved=True,
        moderator=interaction.user,
        original_embed=message.embeds[0] if message.embeds else None
    )

    # Отправляем уведомление пользователю
    await NotificationManager.send_decision_notification(
        user, 
        embed
    )

    # Отправляем сообщение в лог-канал, если это жалоба, запрос или повышение
    try:
        if content_type == "жалоба" and REPORT_LOG_CHANNEL:
            log_channel = interaction.guild.get_channel(REPORT_LOG_CHANNEL)
            if log_channel:
                await LogManager.send_decision_log(
                    channel=log_channel,
                    content_type=content_type,
                    status=status,
                    color=discord.Color.green(),
                    user=user,
                    moderator=interaction.user,
                    original_embed=message.embeds[0] if message.embeds else None
                )
        elif content_type == "запрос" and ORDER_LOG_CHANNEL:
            log_channel = interaction.guild.get_channel(ORDER_LOG_CHANNEL)
            if log_channel:
                await LogManager.send_decision_log(
                    channel=log_channel,
                    content_type=content_type,
                    status=status,
                    color=discord.Color.green(),
                    user=user,
                    moderator=interaction.user,
                    order_id=order_id,
                    order_price=order_price,
                    original_embed=message.embeds[0] if message.embeds else None
                )
        elif content_type == "повышение" and os.getenv('PROMOTION_LOG_CHANNEL'):
            promotion_log_channel_id = int(os.getenv('PROMOTION_LOG_CHANNEL'))
            log_channel = interaction.guild.get_channel(promotion_log_channel_id)
            if log_channel:
                await LogManager.send_decision_log(
                    channel=log_channel,
                    content_type=content_type,
                    status=status,
                    color=discord.Color.green(),
                    user=user,
                    moderator=interaction.user,
                    original_embed=message.embeds[0] if message.embeds else None
                )
    except Exception as e:
        logger.error(f"Ошибка при отправке лога решения: {e}", exc_info=True)
    
    # Используем defer() вместо отправки сообщения
    await interaction.response.defer()
    
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
    Обработка нажатия на кнопку "Отклонить"
    
    Args:
        bot: Бот Discord
        interaction: Объект взаимодействия
        message: Сообщение с кнопками
        user: Пользователь, оставивший заявку
        
    Returns:
        None
    """
    # Отправляем модальное окно для ввода причины отклонения
    modal = RejectReasonModal(message, user)
    await interaction.response.send_modal(modal)

async def handle_reaction_button(bot, interaction):
    """
    Обработка нажатия на кнопку реакции
    
    Args:
        bot: Экземпляр бота
        interaction: Объект взаимодействия с кнопкой
        
    Returns:
        None
    """
    custom_id = interaction.data.get('custom_id', '')
    
    # Получаем канал и сообщение, к которому привязана кнопка
    channel = interaction.channel
    
    try:
        # Ищем сообщение в текущем канале, к которому привязан view
        async for message in channel.history(limit=100):
            if message.author == bot.user and message.components:
                # Проверяем, есть ли в компонентах сообщения кнопка с нужным ID
                for row in message.components:
                    for item in row.children:
                        if item.custom_id == custom_id:
                            # Нашли нужное сообщение с кнопкой
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break
        else:
            logger.warning(f"Не удалось найти сообщение с кнопкой {custom_id}")
            await interaction.response.send_message(
                "Не удалось найти сообщение с этой кнопкой", 
                ephemeral=True
            )
            return
    except Exception as e:
        logger.error(f"Ошибка при поиске сообщения с кнопкой: {e}", exc_info=True)
        await interaction.response.send_message(
            "Произошла ошибка при обработке кнопки", 
            ephemeral=True
        )
        return
    
    # Ищем упоминание пользователя в эмбеде
    user = None
    if message.embeds:
        embed = message.embeds[0]
        # Ищем поле "От кого" или "Заказчик"
        for field in embed.fields:
            if field.name in ["От кого", "👤 Заказчик", "👤 Пользователь"]:
                # Извлекаем ID пользователя из упоминания
                mention = field.value
                user_id_match = re.search(r'<@(\d+)>', mention)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    try:
                        user = await bot.fetch_user(user_id)
                        break
                    except:
                        logger.warning(f"Не удалось получить пользователя с ID {user_id}")
    
    if not user:
        logger.warning("Не удалось определить пользователя из эмбеда")
        await interaction.response.send_message(
            "Не удалось определить автора заявки", 
            ephemeral=True
        )
        return
    
    # Обрабатываем нажатие на кнопку
    if custom_id.startswith("approve_"):
        await handle_approve(bot, interaction, message, user)
    elif custom_id.startswith("reject_"):
        await handle_reject(bot, interaction, message, user)
    else:
        await interaction.response.send_message(
            "Неизвестный тип кнопки", 
            ephemeral=True
        ) 