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
    
    def extract_statics_from_text(self, text):
        """
        Извлекает все числовые статики из текста
        
        Args:
            text: Текст для извлечения статиков
            
        Returns:
            Список найденных статиков
        """
        # Ищем числа длиной от 4 до 6 цифр
        pattern = r'\b\d{4,6}\b'
        return re.findall(pattern, text)
    
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

            logger.info(f"Получен новый ордер от {interaction.user.name} ({interaction.user.id}): {self.order_type_label}")

            # Извлекаем статики из текста и ищем пользователей
            statics = self.extract_statics_from_text(self.game_statics.value)
            found_users = self.find_users_by_statics(statics, interaction.guild)
            
            # Создаем список найденных пользователей
            users_list = []
            for i, (static, member) in enumerate(found_users.items(), 1):
                if member:
                    users_list.append(f"{i}. {static} - {member.mention}")
                else:
                    users_list.append(f"{i}. {static} - Пользователь не найден")
            
            # Создаем embed для отправки в канал ордеров
            order_embed = discord.Embed(
                title=f":identification_card: Ордер: {self.order_type_label}", 
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
            
            # Поле с игровыми статиками, форматируем по-красивее
            formatted_statics = self.game_statics.value.replace("\n", " • ")
            order_embed.add_field(
                name="🎮 Игровые статики",
                value=f"```{formatted_statics}```",
                inline=False
            )
            
            # Добавляем найденных пользователей с эмодзи
            formatted_users = []
            has_found = False
            has_not_found = False
            
            for static, member in found_users.items():
                if member:
                    has_found = True
                    formatted_users.append(f"✅ `{static}` → {member.mention}")
                else:
                    has_not_found = True
                    formatted_users.append(f"❓ `{static}` → Пользователь не найден")
            
            # Если нет статиков, добавляем сообщение об этом
            if not formatted_users:
                users_value = "```Игровые статики не найдены```"
            else:
                # Группируем статики - сначала найденные, потом не найденные
                found_users_list = [u for u in formatted_users if "✅" in u]
                not_found_users_list = [u for u in formatted_users if "❓" in u]
                
                # Добавляем заголовки к каждой группе
                result_parts = []
                
                if found_users_list:
                    result_parts.append("**Найдены:**")
                    result_parts.extend(found_users_list)
                
                if not_found_users_list:
                    if found_users_list:  # Добавляем разделитель, если есть обе группы
                        result_parts.append("\n**Не найдены:**")
                    else:
                        result_parts.append("**Не найдены:**")
                    result_parts.extend(not_found_users_list)
                
                users_value = "\n".join(result_parts)
            
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
            await interaction.followup.send(
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