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
        
        self.add_item(self.game_statics)

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы"""
        try:
            order_data = {
                'order_type': self.order_type_label,
                'order_type_value': self.order_type_value,
                'game_statics': self.game_statics.value
            }

            logger.info(f"Получен новый ордер от {interaction.user.name} ({interaction.user.id}): {self.order_type_label}")

            # Создаем embed для отправки в канал ордеров
            order_embed = discord.Embed(
                title=f"Ордер: {self.order_type_label}", 
                color=discord.Color.blue()
            )
            order_embed.add_field(name="От кого", value=interaction.user.mention, inline=False)
            order_embed.add_field(name="Тип ордера", value=self.order_type_label, inline=False)
            order_embed.add_field(name="Игровые статики", value=self.game_statics.value, inline=False)
            
            # Отправка ордера в общий канал ордеров
            if ORDER_CHANNEL:
                order_channel = interaction.guild.get_channel(ORDER_CHANNEL)
                if order_channel:
                    await order_channel.send(embed=order_embed)
                    logger.info(f"Ордер отправлен в канал {order_channel.name}")
                else:
                    logger.error(f"Канал для ордеров с ID {ORDER_CHANNEL} не найден")
            
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
                    await interaction.response.send_message(
                        f"Ваш ордер успешно создан! Мы рассмотрим его в ближайшее время.",
                        ephemeral=True
                    )
                else:
                    logger.error(f"Не удалось создать канал для ордера от {interaction.user.name}")
                    await interaction.response.send_message(
                        "Произошла ошибка при создании канала для ордера. Но ваш ордер был сохранен.",
                        ephemeral=True
                    )
            else:
                # Если нет категории, просто отправляем сообщение об успехе
                await interaction.response.send_message(
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