import os
import discord

from dotenv import load_dotenv
from tools.logger import Logger
from tools.channel_manager import ChannelManager
from tools.notification_manager import NotificationManager
from tools.embed import EmbedBuilder
from tools.order_utils import OrderUtils

load_dotenv()

logger = Logger.get_instance()

ORDERS_CATEGORY = int(os.getenv('ORDERS_CATEGORY', 0))
ORDER_CHANNEL = int(os.getenv('ORDER_CHANNEL', 0))
ORDER_LOG_CHANNEL = int(os.getenv('ORDER_LOG_CHANNEL', 0))

class OrderModal(discord.ui.Modal):
    """Модальное окно для создания запроса"""

    def __init__(self, order_type_label, order_type_value):
        """
        Инициализация модального окна для запроса
        
        Args:
            order_type_label: Название типа запроса (для отображения)
            order_type_value: Значение типа запроса (для обработки)
        """
        super().__init__(title=f"Запрос: {order_type_label}")
        self.order_type_label = order_type_label
        self.order_type_value = order_type_value
        
        # Определяем, нужно ли поле для ввода суммы
        self.needs_custom_amount = order_type_value in ['car_repair', 'family_purchase', 'car_purchase']

        self.game_statics = discord.ui.TextInput(
            label="Игровые статики",
            placeholder="Укажите ваши игровые статики...",
            required=True,
            style=discord.TextStyle.short,
            max_length=1000
        )
        
        # Добавляем поле для ввода суммы, если это один из специальных типов заказов
        if self.needs_custom_amount:
            self.amount = discord.ui.TextInput(
                label="Сумма",
                placeholder="Укажите требуемую сумму...",
                required=True,
                style=discord.TextStyle.short,
                max_length=100
            )

        self.evidence = discord.ui.TextInput(
            label="Доказательства",
            placeholder="Укажите ссылки на скриншоты/видео или другие доказательства...",
            required=True,
            style=discord.TextStyle.short,
            max_length=1000
        )
        
        self.add_item(self.game_statics)
        # Добавляем поле суммы, если необходимо
        if self.needs_custom_amount:
            self.add_item(self.amount)
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
            
            # Добавляем сумму, если это специальный тип заказа
            if self.needs_custom_amount:
                order_data['amount'] = self.amount.value

            logger.info(f"Получен новый запрос от {interaction.user.name} ({interaction.user.id}): {self.order_type_label}")

            # Извлекаем все статики из текста и ищем пользователей
            statics = OrderUtils.extract_statics(self.game_statics.value)
            found_users = OrderUtils.find_users(statics, interaction.guild)
            
            # Форматируем список пользователей для отображения
            default_value = f"❓ `{self.game_statics.value}` → Пользователь не найден"
            users_value = OrderUtils.format_users_list(found_users, default_value)
            
            # Создаем embed с помощью EmbedBuilder
            order_embed = EmbedBuilder.create_order_embed(
                user=interaction.user,
                order_data=order_data,
                users_value=users_value
            )
            
            # Создаем канал для запроса если есть категория
            if ORDERS_CATEGORY:
                channel_manager = ChannelManager(interaction.guild)
                
                channel = await channel_manager.create_order_channel(
                    user=interaction.user,
                    order_data=order_data,
                    embed=order_embed
                )

                if channel:
                    logger.info(f"Создан канал для запроса: {channel.name}")
                    await NotificationManager.send_submission_notification(interaction.user, order_embed)
                else:
                    logger.error(f"Не удалось создать канал для запроса от {interaction.user.name}")
                    await interaction.followup.send(
                        "Произошла ошибка при создании канала для запроса. Но ваш запрос был сохранен.",
                        ephemeral=True
                    )
            else:
                await interaction.followup.send(
                    f"Ваш запрос успешно отправлен! Мы рассмотрим его в ближайшее время.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке запроса от {interaction.user.name}: {e}", exc_info=True)
            await interaction.followup.send(
                "Произошла ошибка при отправке запроса. Пожалуйста, попробуйте позже.",
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Обработка ошибок при отправке формы"""
        logger.error(f"Ошибка в модальном окне запроса от {interaction.user.name}: {error}", exc_info=True)
        await interaction.response.send_message(
            "Произошла ошибка при отправке запроса. Пожалуйста, попробуйте позже.",
            ephemeral=True
        )

    def get_order_price(self, order_type_value):
        """Возвращает сумму за запрос в зависимости от его типа"""
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