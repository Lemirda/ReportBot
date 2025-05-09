import discord

from report.report_modal import ReportModal

class ReportButton(discord.ui.Button):
    """Кнопка для отправки жалобы"""

    def __init__(self):
        super().__init__(
            label="Жалоба", 
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportModal())