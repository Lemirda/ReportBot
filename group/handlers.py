import discord
from discord.ui import View

from tools.logger import Logger
from group.modal import GroupTimeModal, CustomGroupModal

logger = Logger.get_instance()

async def handle_group_button(interaction: discord.Interaction):
    """Обработчик нажатия на кнопку группы"""
    try:
        # Получаем тип группы из ID кнопки
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "group_собственное_мп":
            # Для собственного МП показываем модальное окно с двумя полями
            modal = CustomGroupModal()
            await interaction.response.send_modal(modal)
        else:
            # Для стандартных групп определяем тип
            group_type = None
            if custom_id == "group_цеха":
                group_type = "Цеха"
            elif custom_id == "group_поставка":
                group_type = "Поставка"
            elif custom_id == "group_дроп":
                group_type = "Дроп"
            elif custom_id == "group_диллеры":
                group_type = "Диллеры"
            
            if group_type:
                # Показываем модальное окно для ввода времени
                modal = GroupTimeModal(group_type)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message(
                    "Неизвестный тип группы. Пожалуйста, попробуйте снова.",
                    ephemeral=True
                )
    
    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки группы: {e}", exc_info=True)
        await interaction.response.send_message(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            ephemeral=True
        ) 