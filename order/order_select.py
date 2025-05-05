import discord

from order.order_modal import OrderModal

class OrderSelect(discord.ui.View):
    """Представление с выпадающим списком для выбора типа ордера"""
    
    def __init__(self):
        super().__init__(timeout=300)  # Таймаут 5 минут
        
        # Добавляем селектор с вариантами ордеров
        self.add_item(OrderTypeSelect())
        
class OrderTypeSelect(discord.ui.Select):
    """Выпадающий список для выбора типа ордера"""
    
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Конспирация II",
                value="conspiracy_2",
                emoji="🕵️"
            ),
            discord.SelectOption(
                label="Конспирация II с активацией контракта",
                value="conspiracy_2_activated",
                emoji="🔐"
            ),
            discord.SelectOption(
                label="Ценный урок",
                value="valuable_lesson",
                emoji="📚"
            ),
            discord.SelectOption(
                label="Ценный урок с активацией контракта",
                value="valuable_lesson_activated",
                emoji="📝"
            ),
            discord.SelectOption(
                label="Ценная партия",
                value="valuable_batch",
                emoji="💎"
            ),
            discord.SelectOption(
                label="Незаконное предприятие",
                value="illegal_business",
                emoji="🏭"
            ),
            discord.SelectOption(
                label="Незаконное предприятие с активацией контракта",
                value="illegal_business_activated",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Гровер I",
                value="grover_1",
                emoji="🌱"
            ),
            discord.SelectOption(
                label="Гровер I с активацией контракта",
                value="grover_1_activated",
                emoji="🌿"
            )
        ]
        
        super().__init__(
            placeholder="Выберите тип ордера",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Получаем выбранный тип ордера
        selected_value = self.values[0]
        selected_option = next((option for option in self.options if option.value == selected_value), None)
        
        if selected_option:
            # Создаем и показываем модальное окно с выбранным типом ордера
            await interaction.response.send_modal(OrderModal(selected_option.label, selected_value)) 