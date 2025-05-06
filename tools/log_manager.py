import discord

from dotenv import load_dotenv
from tools.logger import Logger

load_dotenv()

logger = Logger.get_instance()

class LogManager:
    """Менеджер для отправки сообщений в лог-канал"""

    @staticmethod
    async def send_log_message(bot, user, content_type, action, message=None, reason=None, author=None, log_channel_id=None):
        """
        Отправка сообщения в лог-канал

        Args:
            bot: Экземпляр бота
            user: Пользователь, отправивший заявку
            content_type: Тип заявки (жалоба/предложение/запрос)
            action: Действие (одобрен/одобрена/одобрено/отклонен/отклонена/отклонено)
            message: Сообщение с эмбедом заявки
            reason: Причина отказа (опционально)
            author: Модератор, совершивший действие
            log_channel_id: ID лог-канала
        """

        channel = bot.get_channel(log_channel_id)
        if not channel:
            logger.warning(f"Лог-канал с ID {log_channel_id} не найден")
            return

        # Определяем цвет в зависимости от действия
        color = discord.Color.green() if "одобрен" in action else discord.Color.red()

        # Корректируем форму действия в зависимости от типа контента
        corrected_action = action
        if action in ["одобрена", "отклонена"] and content_type == "запрос":
            corrected_action = "одобрен" if action == "одобрена" else "отклонен"
        elif action in ["одобрена", "отклонена"] and content_type == "предложение":
            corrected_action = "одобрено" if action == "одобрена" else "отклонено"

        embed = discord.Embed(
            title=f"{content_type.capitalize()} {corrected_action}",
            color=color
        )

        embed.add_field(name="От пользователя", value=f"{user.mention} ({user.name})", inline=False)

        if author:
            embed.add_field(name=f"Кем {corrected_action}", value=f"{author.mention} ({author.name})", inline=False)

        # Если есть сообщение с заявкой, добавляем данные из него
        if message and message.embeds:
            original_embed = message.embeds[0]
            for field in original_embed.fields:
                # Не дублируем поле "От кого" и поля статуса
                if field.name not in ["От кого", "Статус", "Причина отказа"]:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)

        # Если есть Причина отказа, добавляем её
        if reason:
            embed.add_field(name="Причина отказа", value=reason, inline=False)

        try:
            await channel.send(embed=embed)
            logger.info(f"Отправлено сообщение в лог-канал о {corrected_action} {content_type}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в лог-канал: {e}", exc_info=True) 