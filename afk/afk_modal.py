import discord
import time
import os

from tools.logger import Logger
from tools.embed import EmbedBuilder

logger = Logger.get_instance()

class AfkModal(discord.ui.Modal, title="АФК"):
    """Модальное окно для отметки АФК"""

    hours = discord.ui.TextInput(
        label="На сколько (в часах)",
        placeholder="Укажите время в часах",
        required=True,
        style=discord.TextStyle.short,
        max_length=3
    )

    reason = discord.ui.TextInput(
        label="Причина",
        placeholder="Укажите причину АФК",
        required=True,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            try:
                hours_value = float(self.hours.value)

                if hours_value <= 0:
                    await interaction.response.send_message("Количество часов должно быть положительным числом!", ephemeral=True)
                    return

                await interaction.response.defer()

            except ValueError:
                await interaction.response.send_message("Введите корректное число часов!", ephemeral=True)
                return

            current_time = int(time.time())
            end_time = current_time + int(hours_value * 3600)

            afk_data = {
                'user': interaction.user,
                'start_timestamp': current_time,
                'end_timestamp': end_time,
                'reason': self.reason.value
            }

            embed = EmbedBuilder.create_afk_embed(afk_data)

            afk_log_channel_id = int(os.getenv('AFK_LOG_CHANNEL'))
            afk_log_channel = interaction.client.get_channel(afk_log_channel_id)

            await afk_log_channel.send(embed=embed)

            logger.info(f"Пользователь {interaction.user.name} отметился как АФК на {self.hours.value} часов. Причина: {self.reason.value}")

        except Exception as e:
            logger.error(f"Ошибка в модальном окне АФК от {interaction.user.name}: {e}", exc_info=True)
            await interaction.followup.send("Произошла ошибка при отправке формы. Пожалуйста, попробуйте позже.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Обработка ошибок при отправке формы"""
        logger.error(f"Ошибка в модальном окне АФК от {interaction.user.name}: {error}", exc_info=True)
        await interaction.response.send_message(
            "Произошла ошибка при отправке формы. Пожалуйста, попробуйте позже.", 
            ephemeral=True
        )