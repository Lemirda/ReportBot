import discord

from order.order_select import OrderSelect

class OrderButton(discord.ui.Button):
    """Кнопка для размещения ордера"""

    def __init__(self):
        super().__init__(
            label="Разместить ордер", 
            style=discord.ButtonStyle.primary,
            custom_id="order_button"
        )

    async def callback(self, interaction: discord.Interaction):
        # Открываем меню выбора типа ордера
        await interaction.response.send_message(
            "Выберите тип ордера:", 
            view=OrderSelect(), 
            ephemeral=True
        ) 