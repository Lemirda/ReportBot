import discord

from order.order_select import OrderSelect

class OrderButton(discord.ui.Button):
    """Кнопка для размещения запроса"""

    def __init__(self):
        super().__init__(
            label="Разместить запрос", 
            style=discord.ButtonStyle.primary,
            custom_id="order_button"
        )

    async def callback(self, interaction: discord.Interaction):
        # Открываем меню выбора типа запроса
        await interaction.response.send_message(
            "Выберите тип запроса:", 
            view=OrderSelect(), 
            ephemeral=True
        ) 