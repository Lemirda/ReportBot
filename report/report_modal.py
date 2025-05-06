import discord

from tools.channel_manager import ChannelManager
from tools.logger import Logger
from tools.notification_manager import NotificationManager
from tools.embed import EmbedBuilder

logger = Logger.get_instance()

class ReportModal(discord.ui.Modal, title="Отправка жалобы"):
    """Модальное окно для отправки жалобы"""

    target = discord.ui.TextInput(
        label="На кого жалоба",
        placeholder="Укажите имя пользователя или ID...",
        required=True,
        style=discord.TextStyle.short,
        max_length=100
    )

    description = discord.ui.TextInput(
        label="Описание проблемы",
        placeholder="Подробно опишите проблему...",
        required=True,
        style=discord.TextStyle.paragraph,
        min_length=100,
        max_length=1000
    )

    evidence = discord.ui.TextInput(
        label="Доказательства",
        placeholder="Ссылки на изображения или видео...",
        required=True,
        style=discord.TextStyle.short,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            report_data = {
                'target': self.target.value,
                'description': self.description.value,
                'evidence': self.evidence.value
            }

            logger.info(f"Получена новая жалоба от {interaction.user.name} ({interaction.user.id})")

            channel_manager = ChannelManager(interaction.guild)
            
            # Создаем embed для канала с помощью EmbedBuilder
            channel_embed = EmbedBuilder.create_report_embed(interaction.user, report_data)
            
            channel = await channel_manager.create_report_channel(interaction.user, report_data, channel_embed)

            if channel:
                await interaction.response.defer()

                await NotificationManager.send_submission_notification(
                    interaction.user, 
                    channel_embed
                )

            else:
                logger.error(f"Не удалось создать канал для жалобы от {interaction.user.name}")

                await interaction.response.send_message(
                    "Произошла ошибка при создании канала для жалобы. Пожалуйста, попробуйте позже.", 
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке жалобы от {interaction.user.name}: {e}", exc_info=True)

            await interaction.response.send_message(
                "Произошла ошибка при отправке жалобы. Пожалуйста, попробуйте позже.", 
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Обработка ошибок при отправке формы"""
        logger.error(f"Ошибка в модальном окне жалобы от {interaction.user.name}: {error}", exc_info=True)

        await interaction.response.send_message(
            "Произошла ошибка при отправке жалобы. Пожалуйста, попробуйте позже.", 
            ephemeral=True
        )