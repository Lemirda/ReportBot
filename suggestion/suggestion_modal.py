import discord

from tools.channel_manager import ChannelManager
from tools.logger import Logger
from tools.notification_manager import NotificationManager
from tools.embed import EmbedBuilder

logger = Logger.get_instance()

class SuggestionModal(discord.ui.Modal, title="Отправка предложения"):
    """Модальное окно для отправки предложения"""

    description = discord.ui.TextInput(
        label="Описание предложения",
        placeholder="Подробно опишите ваше предложение...",
        required=True,
        style=discord.TextStyle.paragraph,
        min_length=100,
        max_length=1500
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            suggestion_data = {
                'description': self.description.value
            }

            logger.info(f"Получено новое предложение от {interaction.user.name} ({interaction.user.id})")

            channel_manager = ChannelManager(interaction.guild)
            
            # Создаем embed для канала с помощью EmbedBuilder
            channel_embed = EmbedBuilder.create_suggestion_embed(interaction.user, suggestion_data)
            
            channel = await channel_manager.create_suggestion_channel(interaction.user, suggestion_data, channel_embed)

            if channel:
                await interaction.response.defer()

                await NotificationManager.send_submission_notification(
                    interaction.user, 
                    channel_embed
                )

            else:
                logger.error(f"Не удалось создать канал для предложения от {interaction.user.name}")

                await interaction.response.send_message(
                    "Произошла ошибка при создании канала для предложения. Пожалуйста, попробуйте позже.", 
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке предложения от {interaction.user.name}: {e}", exc_info=True)

            await interaction.response.send_message(
                "Произошла ошибка при отправке предложения. Пожалуйста, попробуйте позже.", 
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Обработка ошибок при отправке формы"""
        logger.error(f"Ошибка в модальном окне предложения от {interaction.user.name}: {error}", exc_info=True)

        await interaction.response.send_message(
            "Произошла ошибка при отправке предложения. Пожалуйста, попробуйте позже.", 
            ephemeral=True
        )