import discord
from discord.ui import Button, View

class GroupButton(Button):
    """Кнопка для создания группы определенного типа"""
    
    def __init__(self, group_type):
        """
        Инициализация кнопки группы
        
        Args:
            group_type: Тип группы (Цеха, Поставка, Дроп, Диллеры, Собственное МП)
        """
        # Определяем стиль и эмодзи в зависимости от типа группы
        style = discord.ButtonStyle.primary
        emoji = "👥"
        
        if group_type == "Цеха":
            emoji = "🏭"
        elif group_type == "Поставка":
            emoji = "📦"
        elif group_type == "Дроп":
            emoji = "💰"
        elif group_type == "Диллеры":
            emoji = "💊"
        elif group_type == "Собственное МП":
            emoji = "✏️"
            style = discord.ButtonStyle.secondary
        
        super().__init__(
            style=style,
            label=f"Групп {group_type}",
            emoji=emoji,
            custom_id=f"group_{group_type.lower().replace(' ', '_')}"
        )

class GroupView(View):
    """View с кнопками для создания групп"""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        # Добавляем кнопки для разных типов групп
        self.add_item(GroupButton("Цеха"))
        self.add_item(GroupButton("Поставка"))
        self.add_item(GroupButton("Дроп"))
        self.add_item(GroupButton("Диллеры"))
        self.add_item(GroupButton("Собственное МП")) 