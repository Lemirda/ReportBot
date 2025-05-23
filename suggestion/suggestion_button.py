import discord

from suggestion.suggestion_modal import SuggestionModal

class SuggestionButton(discord.ui.Button):
    """Кнопка для отправки предложения"""

    def __init__(self):
        super().__init__(
            label="Предложение", 
            style=discord.ButtonStyle.success, 
            custom_id="suggestion_button"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestionModal())