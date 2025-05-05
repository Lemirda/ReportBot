import discord

from tools.channel_manager import ChannelManager
from tools.logger import Logger
from tools.notification_manager import NotificationManager

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
            channel = await channel_manager.create_report_channel(interaction.user, report_data)

            if channel:
                await interaction.response.defer()

                # Создаем эмбед с информацией о жалобе
                embed = discord.Embed(title="Жалоба", color=discord.Color.red())
                embed.add_field(name="На кого", value=self.target.value, inline=False)
                embed.add_field(name="Описание", value=self.description.value, inline=False)
                embed.add_field(name="Доказательства", value=self.evidence.value, inline=False)
                embed.add_field(name="Статус", value="Ожидает рассмотрения", inline=False)
                embed.set_footer(text="Вы получите уведомление, когда жалоба будет рассмотрена")

                # Отправляем уведомление в ЛС
                notification_sent = await NotificationManager.send_submission_notification(
                    interaction.user, 
                    "жалоба", 
                    embed
                )

                # Если уведомление в ЛС не отправлено, отправляем во временном сообщении
                if not notification_sent:
                    await interaction.followup.send(
                        "Ваша жалоба успешно отправлена! Модераторы рассмотрят её в ближайшее время.",
                        ephemeral=True
                    )
            else:
                logger.error(f"Не удалось создать канал для жалобы от {interaction.user.name}")

                await interaction.response.send_message(
                    "Произошла ошибка при создании канала для жалобы. Пожалуйста, попробуйте позже.", 
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке жалобы от {interaction.user.name}: {e}", exc_info=True)

            try:
                await interaction.response.send_message(
                    "Произошла ошибка при отправке жалобы. Пожалуйста, попробуйте позже.", 
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
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