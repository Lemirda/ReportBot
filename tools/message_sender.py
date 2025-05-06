import discord
from tools.logger import Logger
from tools.view import FeedbackView, OrderView

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

        # Создаем эмбед
        embed = discord.Embed(
            title="Обратная связь",
            description="Используйте кнопки ниже, чтобы отправить жалобу или предложение по улучшению сервера.",
            color=discord.Color.blue()
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1339296664925503503/1368522112137957416/videoPreview.png?ex=68188709&is=68173589&hm=8316d77871c2864e6550bc158c0d8b3e8749bbc6a63322118282d47583832766&")

        embed.add_field(
            name="🚨 Жалоба", 
            value="Нажмите кнопку 'Жалоба', чтобы сообщить о нарушении правил другим пользователем.", 
            inline=False
        )

        embed.add_field(
            name="💡 Предложение",
            value="Нажмите кнопку 'Предложение', чтобы предложить улучшение или новую функцию для сервера.",
            inline=False
        )

        # Создаем view и отправляем эмбед
        view = FeedbackView(self.bot)
        return await self.send_embed(channel, embed, view) 

    async def send_order_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопкой запроса"""
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        embed = discord.Embed(
            title="Запросы",
            description="Используйте кнопку ниже, чтобы разместить запрос.",
            color=discord.Color.blue()
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1339296664925503503/1368522112137957416/videoPreview.png?ex=68188709&is=68173589&hm=8316d77871c2864e6550bc158c0d8b3e8749bbc6a63322118282d47583832766&")
        
        embed.add_field(
            name="📋 Запрос",
            value="Нажмите кнопку 'Разместить запрос', чтобы создать заявку на выполнение миссии.",
            inline=False
        )

        view = OrderView(self.bot)
        return await self.send_embed(channel, embed, view) 