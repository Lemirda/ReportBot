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
                description="Ордер на Конспирацию II",
                value="conspiracy_2",
                emoji="🕵️"
            ),
            discord.SelectOption(
                label="Конспирация II с активацией контракта",
                description="Ордер на Конспирацию II с активацией",
                value="conspiracy_2_activated",
                emoji="🔐"
            ),
            discord.SelectOption(
                label="Ценный урок",
                description="Ордер на Ценный урок",
                value="valuable_lesson",
                emoji="📚"
            ),
            discord.SelectOption(
                label="Ценный урок с активацией контракта",
                description="Ордер на Ценный урок с активацией",
                value="valuable_lesson_activated",
                emoji="📝"
            ),
            discord.SelectOption(
                label="Ценная партия",
                description="Ордер на Ценную партию",
                value="valuable_batch",
                emoji="💎"
            ),
            discord.SelectOption(
                label="Незаконное предприятие",
                description="Ордер на Незаконное предприятие",
                value="illegal_business",
                emoji="🏭"
            ),
            discord.SelectOption(
                label="Незаконное предприятие с активацией контракта",
                description="Ордер на Незаконное предприятие с активацией",
                value="illegal_business_activated",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Гровер I",
                description="Ордер на Гровер I",
                value="grover_1",
                emoji="🌱"
            ),
            discord.SelectOption(
                label="Гровер I с активацией контракта",
                description="Ордер на Гровер I с активацией",
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