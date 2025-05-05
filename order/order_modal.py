import os
import discord

from dotenv import load_dotenv
from tools.logger import Logger
from tools.channel_manager import ChannelManager
from tools.notification_manager import NotificationManager

load_dotenv()

logger = Logger.get_instance()
ORDERS_CATEGORY = int(os.getenv('ORDERS_CATEGORY', 0))
ORDER_CHANNEL = int(os.getenv('ORDER_CHANNEL', 0))
ORDER_LOG_CHANNEL = int(os.getenv('ORDER_LOG_CHANNEL', 0))

class OrderModal(discord.ui.Modal):
    """Модальное окно для создания ордера"""

    def __init__(self, order_type_label, order_type_value):
        """
        Инициализация модального окна для ордера
        
        Args:
            order_type_label: Название типа ордера (для отображения)
            order_type_value: Значение типа ордера (для обработки)
        """
        super().__init__(title=f"Ордер: {order_type_label}")
        self.order_type_label = order_type_label
        self.order_type_value = order_type_value
        
        # Поле для указания игровых статиков
        self.game_statics = discord.ui.TextInput(
            label="Игровые статики",
            placeholder="Укажите ваши игровые статики...",
            required=True,
            style=discord.TextStyle.short,
            max_length=1000
        )
        
        # Поле для указания доказательств
        self.evidence = discord.ui.TextInput(
            label="Доказательства",
            placeholder="Укажите ссылки на скриншоты/видео или другие доказательства...",
            required=True,
            style=discord.TextStyle.short,
            max_length=1000
        )
        
        self.add_item(self.game_statics)
        self.add_item(self.evidence)

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            # Сначала подтверждаем получение формы
            await interaction.response.defer(ephemeral=True)
            
            order_data = {
                'order_type': self.order_type_label,
                'order_type_value': self.order_type_value,
                'game_statics': self.game_statics.value,
                'evidence': self.evidence.value
            }

            logger.info(f"Получен новый ордер от {interaction.user.name} ({interaction.user.id}): {self.order_type_label}")

            # Создаем embed для отправки в канал ордеров
            order_embed = discord.Embed(
                title=f"Ордер: {self.order_type_label}", 
                color=discord.Color.blue()
            )
            order_embed.add_field(name="От кого", value=interaction.user.mention, inline=False)
            
            order_embed.add_field(name="Игровые статики", value=self.game_statics.value, inline=False)
            
            # Добавляем тип ордера
            order_embed.add_field(name="Тип ордера", value=self.order_type_label, inline=False)
            
            # Добавляем сумму
            order_price = self.get_order_price(self.order_type_value)
            order_embed.add_field(name="Сумма", value=order_price, inline=False)
            
            # Добавляем доказательства
            order_embed.add_field(name="Доказательства", value=self.evidence.value if self.evidence.value else "Не предоставлены", inline=False)
            
            # Создаем канал для ордера если есть категория
            if ORDERS_CATEGORY:
                channel_manager = ChannelManager(interaction.guild)
                
                channel = await channel_manager.create_order_channel(
                    user=interaction.user,
                    order_data=order_data,
                    embed=order_embed
                )

                if channel:
                    logger.info(f"Создан канал для ордера: {channel.name}")
                    # Отправляем уведомление пользователю
                    await NotificationManager.send_submission_notification(interaction.user, order_embed)
                    
                else:
                    logger.error(f"Не удалось создать канал для ордера от {interaction.user.name}")
                    await interaction.followup.send(
                        "Произошла ошибка при создании канала для ордера. Но ваш ордер был сохранен.",
                        ephemeral=True
                    )
            else:
                await interaction.followup.send(
                    f"Ваш ордер успешно отправлен! Мы рассмотрим его в ближайшее время.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке ордера от {interaction.user.name}: {e}", exc_info=True)
            await interaction.response.send_message(
                "Произошла ошибка при отправке ордера. Пожалуйста, попробуйте позже.",
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Обработка ошибок при отправке формы"""
        logger.error(f"Ошибка в модальном окне ордера от {interaction.user.name}: {error}", exc_info=True)
        await interaction.response.send_message(
            "Произошла ошибка при отправке ордера. Пожалуйста, попробуйте позже.",
            ephemeral=True
        )

    def get_order_price(self, order_type_value):
        """Возвращает сумму за ордер в зависимости от его типа"""
        prices = {
            "conspiracy_2": "150.000-190.000",
            "conspiracy_2_activated": "150.000-190.000 + 15.000",
            "valuable_lesson": "80.000-100.000",
            "valuable_lesson_activated": "80.000-100.000 + 5.000",
            "valuable_batch": "178.000",
            "illegal_business": "174.000",
            "illegal_business_activated": "189.000",
            "grover_1": "137.000",
            "grover_1_activated": "142.000"
        }
        return prices.get(order_type_value, "Цена не указана") 