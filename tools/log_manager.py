import os
import discord
from dotenv import load_dotenv
from tools.logger import Logger

load_dotenv()

logger = Logger.get_instance()
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL', 0))

class LogManager:
    """Менеджер для отправки сообщений в лог-канал"""

    @staticmethod
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