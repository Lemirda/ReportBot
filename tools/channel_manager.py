import os
import discord

from dotenv import load_dotenv

from tools.logger import Logger
from tools.reaction_handlers import ReactionView
from database.db_manager import DatabaseManager

logger = Logger.get_instance()
db_manager = DatabaseManager.get_instance()

class ChannelManager:
    """Класс для управления каналами с жалобами, предложениями и запросами"""

    def __init__(self, guild: discord.Guild):
        self.guild = guild

        load_dotenv()

        self.reports_category_id = int(os.getenv('REPORTS_CATEGORY'))
        self.suggestions_category_id = int(os.getenv('SUGGESTIONS_CATEGORY'))
        self.orders_category_id = int(os.getenv('ORDERS_CATEGORY', 0))

        self.report_role_ids = [role_id.strip() for role_id in os.getenv('REPORT_PING_ROLES', '').split(',') if role_id.strip()]
        self.suggestion_role_ids = [role_id.strip() for role_id in os.getenv('SUGGESTION_PING_ROLES', '').split(',') if role_id.strip()]
        self.order_role_ids = [role_id.strip() for role_id in os.getenv('ORDER_PING_ROLES', '').split(',') if role_id.strip()]

    def get_role_mentions(self, role_ids):
        """
        Получение упоминаний ролей по их ID

        Args:
            role_ids: Список ID ролей

        Returns:
            Строка с упоминаниями ролей
        """
        mentions = []

        for role_id in role_ids:
            try:
                role_id_int = int(role_id)
                role = self.guild.get_role(role_id_int)

                if role:
                    mentions.append(role.mention)
                else:
                    logger.warning(f"Роль с ID {role_id} не найдена")
            except ValueError:
                logger.warning(f"Некорректный ID роли: {role_id}")

        return ' '.join(mentions)
        
    async def create_channel(self, channel_type: str, user: discord.User, data: dict, embed: discord.Embed):
        """
        Универсальный метод создания канала для жалоб, предложений или запросов

        Args:
            channel_type: Тип канала ('жалоба', 'предложение' или 'запрос')
            user: Пользователь, отправивший запрос
            data: Данные запроса (словарь с полями)
            embed: Готовый embed для отправки

        Returns:
            Созданный канал или None, если не удалось создать
        """
        try:
            if channel_type == "жалоба":
                category_id = self.reports_category_id
                role_ids = self.report_role_ids
            elif channel_type == "предложение":
                category_id = self.suggestions_category_id
                role_ids = self.suggestion_role_ids
            elif channel_type == "запрос":
                category_id = self.orders_category_id
                role_ids = self.order_role_ids
            else:
                logger.error(f"Неизвестный тип канала: {channel_type}")
                return None
                
            category = self.guild.get_channel(category_id)

            if not category:
                logger.error(f"Категория для '{channel_type}' с ID {category_id} не найдена")
                return None

            channel_name = f"{channel_type}-{user.name.lower()}"
            channel_name = ''.join(c for c in channel_name if c.isalnum() or c == '-')

            if len(channel_name) > 100:
                channel_name = channel_name[:90]

            access_roles = []

            for role_id in role_ids:
                try:
                    role = self.guild.get_role(int(role_id))

                    if role:
                        access_roles.append(role)
                except ValueError:
                    logger.warning(f"Некорректный ID роли: {role_id}")

            # Создаем разрешения для канала
            overwrites = {
                self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                self.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Добавляем разрешения для ролей
            for role in access_roles:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await self.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )

            logger.info(f"Создан канал для '{channel_type}': {channel.name} (ID: {channel.id})")

            role_mentions = self.get_role_mentions(role_ids)

            # Создаем представление с кнопками
            reaction_view = ReactionView(None, user, channel_type)

            # Отправляем сообщение с эмбедом и кнопками
            message = await channel.send(content=role_mentions, embed=embed, view=reaction_view)
            logger.info(f"Отправлено сообщение с '{channel_type}' в канал {channel.name}")

            db_manager.add_reaction_buttons(
                message.id,
                channel.id,
                channel_type,
                reaction_view.approve_id,
                reaction_view.reject_id
            )

            return channel

        except Exception as e:
            logger.error(f"Ошибка при создании канала для '{channel_type}' от {user.name}: {e}", exc_info=True)
            return None

    async def create_report_channel(self, user: discord.User, report_data: dict, embed: discord.Embed):
        """
        Создание канала для жалобы

        Args:
            user: Пользователь, отправивший жалобу
            report_data: Данные жалобы (словарь с полями)
            embed: Готовый embed для отправки

        Returns:
            Созданный канал или None, если не удалось создать
        """
        return await self.create_channel("жалоба", user, report_data, embed)

    async def create_suggestion_channel(self, user: discord.User, suggestion_data: dict, embed: discord.Embed):
        """
        Создание канала для предложения

        Args:
            user: Пользователь, отправивший предложение
            suggestion_data: Данные предложения (словарь с полями)
            embed: Готовый embed для отправки

        Returns:
            Созданный канал или None, если не удалось создать
        """
        return await self.create_channel("предложение", user, suggestion_data, embed)

    async def create_order_channel(self, user: discord.User, order_data: dict, embed: discord.Embed):
        """
        Создание канала для запроса

        Args:
            user: Пользователь, отправивший запрос
            order_data: Данные запроса (словарь с полями)
            embed: Готовый embed для отправки

        Returns:
            Созданный канал или None, если не удалось создать
        """
        return await self.create_channel("запрос", user, order_data, embed)