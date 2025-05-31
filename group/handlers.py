import discord
from discord.ui import View
import os

from tools.logger import Logger
from group.modal import GroupTimeModal, CustomGroupModal

logger = Logger.get_instance()

async def handle_group_button(interaction: discord.Interaction):
    """Обработчик нажатия на кнопку группы"""
    try:
        # Проверяем, есть ли у пользователя необходимые роли
        allowed_roles_str = os.getenv('GROUP_ALLOWED_ROLES', '')
        if allowed_roles_str:
            allowed_role_ids = [int(role_id) for role_id in allowed_roles_str.split(',') if role_id]
            
            # Проверяем наличие ролей у пользователя
            user_has_permission = False
            for role in interaction.user.roles:
                if role.id in allowed_role_ids:
                    user_has_permission = True
                    break
            
            if not user_has_permission:
                await interaction.response.send_message(
                    "У вас нет доступа к этой функции. Требуется специальная роль.",
                    ephemeral=True
                )
                logger.warning(f"Пользователь {interaction.user.display_name} попытался использовать кнопку группы без необходимых ролей")
                return
        
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