import discord

from tools.logger import Logger
from tools.channel_manager import ChannelManager
from tools.embed import EmbedBuilder
from tools.notification_manager import NotificationManager

logger = Logger.get_instance()

class PromotionModal(discord.ui.Modal):
    """Модальное окно для заявки на повышение"""

    def __init__(self, current_rank, next_rank):
        super().__init__(title=f"Повышение с {current_rank} до {next_rank} ранга")
        self.current_rank = current_rank
        self.next_rank = next_rank
        
        # Поля для заполнения
        self.missions = discord.ui.TextInput(
            label="МП в которых участвовал",
            placeholder="Перечислите МП, в которых вы принимали участие",
            required=True,
            style=discord.TextStyle.paragraph
        )
        
        self.links = discord.ui.TextInput(
            label="Ссылка на откаты",
            placeholder="Укажите ссылки на скриншоты откатов",
            required=True,
            style=discord.TextStyle.short,
            max_length=1000
        )
        
        self.rules = discord.ui.TextInput(
            label="Ознакомлен с правилами?",
            placeholder="Да/Нет",
            required=True,
            style=discord.TextStyle.short,
            max_length=10
        )
        
        self.days = discord.ui.TextInput(
            label="Сколько дней в фаме?",
            placeholder="Укажите количество дней",
            required=True,
            style=discord.TextStyle.short,
            max_length=10
        )
        
        self.evidence = discord.ui.TextInput(
            label="Доказательства",
            placeholder="Ссылки на скриншоты или другие доказательства",
            required=True,
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.missions)
        self.add_item(self.links)
        self.add_item(self.rules)
        self.add_item(self.days)
        self.add_item(self.evidence)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            # Откладываем ответ пользователю
            await interaction.response.defer(ephemeral=True)

            promotion_data = {
                'current_rank': self.current_rank,
                'next_rank': self.next_rank,
                'missions': self.missions.value,
                'links': self.links.value,
                'rules': self.rules.value,
                'days': self.days.value,
                'evidence': self.evidence.value
            }

            embed = EmbedBuilder.create_promotion_embed(interaction.user, promotion_data)
            
            # Создаем канал для рассмотрения заявки
            channel_manager = ChannelManager(interaction.guild)
            
            # Создаем канал для заявки
            channel = await channel_manager.create_promotion_channel(
                interaction.user, 
                promotion_data, 
                embed
            )
            
            if channel:
                logger.info(f"Пользователь {interaction.user.name} создал заявку на повышение с {self.current_rank} до {self.next_rank} ранга")
                
                # Отправляем уведомление пользователю в личные сообщения
                await NotificationManager.send_submission_notification(
                    interaction.user,
                    embed
                )
            else:
                await interaction.followup.send("Не удалось создать канал для заявки. Пожалуйста, обратитесь к администрации.", ephemeral=True)
                logger.error(f"Не удалось создать канал для заявки пользователя {interaction.user.name}")
        
        except Exception as e:
            logger.error(f"Ошибка в модальном окне повышения от {interaction.user.name}: {e}", exc_info=True)
            await interaction.followup.send("Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Обработка ошибок при отправке формы"""
        logger.error(f"Ошибка в модальном окне повышения от {interaction.user.name}: {error}", exc_info=True)
        await interaction.response.send_message(
            "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже.", 
            ephemeral=True
        ) 