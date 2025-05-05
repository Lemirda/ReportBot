import os
import discord

from dotenv import load_dotenv

from tools.logger import Logger
from tools.reaction_utils import ReactionView
from database.db_manager import DatabaseManager

logger = Logger.get_instance()
db_manager = DatabaseManager.get_instance()

class ChannelManager:
    """Класс для управления каналами с жалобами и предложениями"""

    def __init__(self, guild: discord.Guild):
        self.guild = guild

        load_dotenv()

        self.reports_category_id = int(os.getenv('REPORTS_CATEGORY', 0))
        self.suggestions_category_id = int(os.getenv('SUGGESTIONS_CATEGORY', 0))

        self.report_role_ids = [role_id.strip() for role_id in os.getenv('REPORT_PING_ROLES', '').split(',') if role_id.strip()]
        self.suggestion_role_ids = [role_id.strip() for role_id in os.getenv('SUGGESTION_PING_ROLES', '').split(',') if role_id.strip()]

    def _get_role_mentions(self, role_ids):
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

    async def create_report_channel(self, user: discord.User, report_data: dict):
        """
        Создание канала для жалобы

        Args:
            user: Пользователь, отправивший жалобу
            report_data: Данные жалобы (словарь с полями)

        Returns:
            Созданный канал или None, если не удалось создать
        """
        try:
            category = self.guild.get_channel(self.reports_category_id)

            if not category:
                logger.error(f"Категория для жалоб с ID {self.reports_category_id} не найдена")
                return None

            channel_name = f"жалоба-{user.name.lower()}"
            channel_name = ''.join(c for c in channel_name if c.isalnum() or c == '-')

            if len(channel_name) > 100:
                channel_name = channel_name[:90]

            # Получаем роли, которые будут иметь доступ к каналу
            access_roles = []

            for role_id in self.report_role_ids:
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

            logger.info(f"Создан канал для жалобы: {channel.name} (ID: {channel.id})")

            embed = discord.Embed(title="Жалоба", color=discord.Color.red())
            embed.add_field(name="От кого", value=user.mention, inline=False)
            embed.add_field(name="На кого", value=report_data.get('target', 'Не указано'), inline=False)
            embed.add_field(name="Описание", value=report_data.get('description', 'Не указано'), inline=False)
            embed.add_field(name="Доказательства", value=report_data.get('evidence', 'Не указано'), inline=False)

            role_mentions = self._get_role_mentions(self.report_role_ids)

            # Создаем представление с кнопками
            reaction_view = ReactionView(None, user, "жалоба")

            # Отправляем сообщение с эмбедом и кнопками
            message = await channel.send(content=role_mentions, embed=embed, view=reaction_view)
            logger.info(f"Отправлено сообщение с жалобой в канал {channel.name}")

            db_manager.add_reaction_buttons(
                message.id,
                channel.id,
                "жалоба",
                reaction_view.approve_id,
                reaction_view.reject_id
            )

            return channel

        except Exception as e:
            logger.error(f"Ошибка при создании канала для жалобы от {user.name}: {e}", exc_info=True)
            return None

    async def create_suggestion_channel(self, user: discord.User, suggestion_data: dict):
        """
        Создание канала для предложения

        Args:
            user: Пользователь, отправивший предложение
            suggestion_data: Данные предложения (словарь с полями)

        Returns:
            Созданный канал или None, если не удалось создать
        """
        try:
            category = self.guild.get_channel(self.suggestions_category_id)

            if not category:
                logger.error(f"Категория для предложений с ID {self.suggestions_category_id} не найдена")
                return None

            channel_name = f"предложение-{user.name.lower()}"
            channel_name = ''.join(c for c in channel_name if c.isalnum() or c == '-')

            if len(channel_name) > 100:
                channel_name = channel_name[:90]

            # Получаем роли, которые будут иметь доступ к каналу
            access_roles = []

            for role_id in self.suggestion_role_ids:
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

            logger.info(f"Создан канал для предложения: {channel.name} (ID: {channel.id})")

            embed = discord.Embed(title="Предложение", color=discord.Color.green())
            embed.add_field(name="От кого", value=user.mention, inline=False)
            embed.add_field(name="Описание", value=suggestion_data.get('description', 'Не указано'), inline=False)

            role_mentions = self._get_role_mentions(self.suggestion_role_ids)

            # Создаем представление с кнопками
            reaction_view = ReactionView(None, user, "предложение")

            # Отправляем сообщение с эмбедом и кнопками
            message = await channel.send(content=role_mentions, embed=embed, view=reaction_view)
            logger.info(f"Отправлено сообщение с предложением в канал {channel.name}")

            db_manager.add_reaction_buttons(
                message.id,
                channel.id,
                "предложение",
                reaction_view.approve_id,
                reaction_view.reject_id
            )

            return channel

        except Exception as e:
            logger.error(f"Ошибка при создании канала для предложения от {user.name}: {e}", exc_info=True)
            return None