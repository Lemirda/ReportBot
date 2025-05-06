import discord
from tools.logger import Logger
from tools.view import FeedbackView, OrderView
from tools.embed import EmbedBuilder

logger = Logger.get_instance()

class MessageSender:
    """Класс для отправки сообщений и эмбедов в каналы Discord"""

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def clear_channel(self, channel: discord.TextChannel):
        """Очищает канал от сообщений"""
        try:
            if isinstance(channel, discord.TextChannel):
                async for message in channel.history(limit=None):
                    await message.delete()
                logger.info(f"Сообщения в канале {channel.name} очищены")
        except Exception as e:
            logger.error(f"Ошибка при очистке канала: {e}", exc_info=True)

    async def send_embed(self, channel: discord.abc.Messageable, embed: discord.Embed, view=None):
        """Отправляет эмбед в указанный канал с опциональным view"""
        try:
            sent_message = await channel.send(embed=embed, view=view)
            logger.info(f"Отправлено сообщение с эмбедом в канал {getattr(channel, 'name', channel.id)}")
            return sent_message
        except Exception as e:
            logger.error(f"Ошибка при отправке эмбеда: {e}", exc_info=True)
            return None

    async def send_report_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопками обратной связи"""
        # Сначала очищаем канал, если это текстовый канал
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        # Создаем эмбед с помощью EmbedBuilder
        embed = EmbedBuilder.create_feedback_embed()

        # Создаем view и отправляем эмбед
        view = FeedbackView(self.bot)
        return await self.send_embed(channel, embed, view)

    async def send_order_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопкой запроса"""
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        # Создаем эмбед с помощью EmbedBuilder
        embed = EmbedBuilder.create_order_button_embed()

        view = OrderView(self.bot)
        return await self.send_embed(channel, embed, view) 