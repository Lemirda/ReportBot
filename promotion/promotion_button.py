import discord
import os

from promotion.promotion_modal import PromotionModal
from tools.logger import Logger

logger = Logger.get_instance()

class PromotionButton(discord.ui.Button):
    """Кнопка для отправки заявки на повышение"""

    def __init__(self):
        super().__init__(
            label="Повышение", 
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            user_roles = [role.id for role in interaction.user.roles]
            
            # Получаем ID ролей рангов из .env
            rank_5 = int(os.getenv('RANK_5'))
            rank_4 = int(os.getenv('RANK_4'))
            rank_3 = int(os.getenv('RANK_3'))
            rank_2 = int(os.getenv('RANK_2'))
            rank_1 = int(os.getenv('RANK_1'))
            
            # Определяем текущий ранг и следующий
            current_rank = 0
            next_rank = 0
            
            if rank_5 in user_roles:
                current_rank = 5
                next_rank = 0  # Максимальный ранг
            elif rank_4 in user_roles:
                current_rank = 4
                next_rank = 5
            elif rank_3 in user_roles:
                current_rank = 3
                next_rank = 4
            elif rank_2 in user_roles:
                current_rank = 2
                next_rank = 3
            elif rank_1 in user_roles:
                current_rank = 1
                next_rank = 2
            else:
                current_rank = 0
                next_rank = 0

            # Если у пользователя нет ролей с 1 по 5 или у него 5 ранг
            if current_rank == 0 or current_rank == 5:
                await interaction.response.send_message(
                    "Дальнейшее продвижение возможно только в индивидуальном порядке. Обратитесь к рангам выше.",
                    ephemeral=True
                )
                return

            await interaction.response.send_modal(PromotionModal(current_rank, next_rank))
            
        except Exception as e:
            logger.error(f"Ошибка при обработке кнопки повышения: {e}", exc_info=True)
            await interaction.response.send_message(
                "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
                ephemeral=True
            ) 