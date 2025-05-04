import discord

from ui.components.base_button import BaseButton
from report.report_modal import ReportModal

class ReportButton(BaseButton):
    """Кнопка для отправки жалобы"""

    def __init__(self):
        super().__init__(
            label="Жалоба", 
            style=discord.ButtonStyle.danger,
            custom_id="report_button"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportModal())