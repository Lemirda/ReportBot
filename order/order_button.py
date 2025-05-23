import discord

from order.order_select import OrderSelect

class OrderButton(discord.ui.Button):
    """Кнопка для размещения запроса"""

    def __init__(self):
        super().__init__(
            label="Разместить запрос", 
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Выберите тип запроса:", 
            view=OrderSelect(), 
            ephemeral=True,
            delete_after=30
        )