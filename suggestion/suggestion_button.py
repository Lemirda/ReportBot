import discord

from ui.components.base_button import BaseButton
from suggestion.suggestion_modal import SuggestionModal

class SuggestionButton(BaseButton):
    """Кнопка для отправки предложения"""

    def __init__(self):
        super().__init__(
            label="Предложение", 
            style=discord.ButtonStyle.success, 
            custom_id="suggestion_button"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestionModal())