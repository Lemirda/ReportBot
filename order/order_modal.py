import os
import discord
import re

from dotenv import load_dotenv
from tools.logger import Logger
from tools.channel_manager import ChannelManager
from tools.notification_manager import NotificationManager
from database.user import UserManager

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
    
    def extract_statics_from_text(self, text):
        """
        Извлекает все потенциальные статики из текста
        
        Args:
            text: Текст для извлечения статиков
            
        Returns:
            Список найденных статиков
        """
        # Извлекаем все отдельные слова как потенциальные статики
        words = re.findall(r'\b\w+\b', text)
        
        # Если текст не содержит отдельных слов, возвращаем весь текст как один статик
        if not words and text.strip():
            return [text.strip()]
            
        return words
    
    def find_users_by_statics(self, statics, guild):
        """
        Ищет пользователей по списку статиков
        
        Args:
            statics: Список статиков для поиска
            guild: Объект сервера Discord
            
        Returns:
            Словарь {статик: пользователь или None}
        """
        user_manager = UserManager.get_instance()
        found_users = {}
        
        for static in statics:
            # Пробуем найти пользователя сначала по точному совпадению
            users = user_manager.get_user_by_game_static(static)
            if users and len(users) > 0:
                # Попытаемся найти пользователя на сервере
                user_id = users[0]['id']
                member = guild.get_member(user_id)
                if member:
                    found_users[static] = member
                else:
                    found_users[static] = None
            else:
                found_users[static] = None
                
        return found_users

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

            logger.info(f"Получен новый запрос от {interaction.user.name} ({interaction.user.id}): {self.order_type_label}")

            # Извлекаем все статики из текста и ищем пользователей
            statics = self.extract_statics_from_text(self.game_statics.value)
            found_users = self.find_users_by_statics(statics, interaction.guild)
            
            # Создаем список найденных и ненайденных пользователей
            users_list = []
            
            if found_users:
                for static, member in found_users.items():
                    if member:
                        users_list.append(f"✅ `{static}` → {member.mention}")
                    else:
                        users_list.append(f"❓ `{static}` → Пользователь не найден")
                
                users_value = "\n".join(users_list)
            else:
                # Если не нашли статиков, берем весь текст как один статик
                users_value = f"❓ `{self.game_statics.value}` → Пользователь не найден"
            
            # Создаем embed для отправки в канал запросов
            order_embed = discord.Embed(
                title=f":identification_card: Запрос: {self.order_type_label}", 
                color=0x3498db  # Яркий синий цвет
            )
            
            # Добавляем текущую дату и время
            from datetime import datetime
            current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Поле информации о заказчике
            order_embed.add_field(
                name="👤 Заказчик",
                value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
                inline=False
            )
            
            # Поле с типом и ценой
            order_embed.add_field(
                name="💰 Информация",
                value=f"**Тип:** {self.order_type_label}\n**Стоимость:** {self.get_order_price(self.order_type_value)}",
                inline=False
            )
            
            # Поле с пользователями по статикам
            order_embed.add_field(
                name="🔍 Пользователи по статикам",
                value=users_value,
                inline=False
            )
            
            # Доказательства с форматированием
            order_embed.add_field(
                name="📷 Доказательства",
                value=f"```{self.evidence.value}```",
                inline=False
            )
            
            # Устанавливаем футер с ID заказа и временем
            order_id = f"ORD-{interaction.user.id}-{int(datetime.now().timestamp())}"
            order_embed.set_footer(text=f"ID заказа: {order_id} • {current_time}")
            
            # Добавляем уменьшенный аватар пользователя
            if interaction.user.avatar:
                order_embed.set_thumbnail(url=interaction.user.avatar.url)
            
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