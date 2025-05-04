import discord

from ui.components.main_view import MainView
from utils.logger import Logger

logger = Logger.get_instance()

class EmbedMessageHandler:
    """Обработчик для эмбеда с кнопками жалобы и предложения"""

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def send_main_embed(self, channel: discord.abc.Messageable):
        """
        Отправка основного эмбеда с кнопками

        Args:
            channel: Канал для отправки сообщения
        """
        # Удаляем все предыдущие сообщения в канале
        try:
            if isinstance(channel, discord.TextChannel):
                # Получаем и удаляем все сообщения в канале
                async for message in channel.history(limit=None):
                    await message.delete()

                logger.info(f"Сообщения в канале {channel.name} очищены")
        except Exception as e:
            logger.error(f"Ошибка при очистке канала: {e}", exc_info=True)

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

        view = MainView(self.bot)

        await channel.send(embed=embed, view=view)
        logger.info(f"Отправлено сообщение с кнопками обратной связи в канал {getattr(channel, 'name', channel.id)}")