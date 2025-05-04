import discord

from utils.channel_manager import ChannelManager
from utils.logger import Logger

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
            channel = await channel_manager.create_suggestion_channel(interaction.user, suggestion_data)

            if channel:
                await interaction.response.defer()

                try:
                    embed = discord.Embed(title="Предложение", color=discord.Color.green())
                    embed.add_field(name="Описание", value=self.description.value, inline=False)
                    embed.add_field(name="Статус", value="Ожидает рассмотрения", inline=False)
                    embed.set_footer(text="Вы получите уведомление, когда предложение будет рассмотрено")

                    await interaction.user.send(content="Ваша заявка отправлена на рассмотрение:", embed=embed)

                    logger.info(f"Отправлено уведомление в ЛС пользователю {interaction.user.name}")
                except Exception as dm_error:
                    logger.warning(f"Не удалось отправить сообщение в ЛС пользователю {interaction.user.name}: {dm_error}")

                    await interaction.followup.send(
                        "Ваше предложение успешно отправлено! Спасибо за обратную связь.",
                        ephemeral=True
                    )
            else:
                logger.error(f"Не удалось создать канал для предложения от {interaction.user.name}")

                await interaction.response.send_message(
                    "Произошла ошибка при создании канала для предложения. Пожалуйста, попробуйте позже.", 
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке предложения от {interaction.user.name}: {e}", exc_info=True)

            try:
                await interaction.response.send_message(
                    "Произошла ошибка при отправке предложения. Пожалуйста, попробуйте позже.", 
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
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