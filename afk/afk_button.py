import discord

from afk.afk_modal import AfkModal

class AfkButton(discord.ui.Button):
    """Кнопка для отметки АФК"""

    def __init__(self):
        super().__init__(
            label="Отметится", 
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AfkModal())