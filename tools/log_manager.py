import discord

from dotenv import load_dotenv
from tools.logger import Logger
from tools.embed import EmbedBuilder

load_dotenv()

logger = Logger.get_instance()

class LogManager:
    """Менеджер для отправки сообщений в лог-канал"""

    @staticmethod
    async def send_decision_log(channel, content_type, status, color, user, moderator, 
                              original_embed=None, reason=None, order_id=None, order_price=None):
        """
        Отправка информации о решении в лог-канал
        
        Args:
            channel: Канал для отправки лога
            content_type: Тип заявки (жалоба/предложение/запрос)
            status: Статус заявки (одобрен/одобрена/одобрено/отклонен/отклонена/отклонено)
            color: Цвет эмбеда (discord.Color)
            user: Пользователь, создавший заявку
            moderator: Модератор, принявший решение
            original_embed: Оригинальный эмбед заявки
            reason: Причина отказа (если заявка отклонена)
            order_id: ID заказа (для запросов)
            order_price: Цена заказа (для запросов)
        """
        if not channel:
            logger.warning(f"Лог-канал не найден")
            return
            
        embed = discord.Embed(
            title=f"{content_type.capitalize()} {status}",
            color=color
        )
        
        # Информация о пользователе и модераторе
        embed.add_field(name="От пользователя", value=f"{user.mention} ({user.name})", inline=False)
        embed.add_field(name=f"Модератор", value=f"{moderator.mention} ({moderator.name})", inline=False)
        
        # Информация о заказе (если это запрос)
        if content_type == "запрос":
            if order_id:
                embed.add_field(name="ID заказа", value=order_id, inline=True)
            if order_price:
                embed.add_field(name="Стоимость", value=order_price, inline=True)
        
        # Добавляем поля из оригинального эмбеда
        if original_embed:
            for field in original_embed.fields:
                # Исключаем поля, которые уже добавили или не нужны в логе
                if field.name not in ["От кого", "👤 Заказчик", "Статус", "Причина отказа"]:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
        
        # Добавляем причину отказа, если есть
        if reason:
            embed.add_field(name="Причина отказа", value=reason, inline=False)
        
        try:
            await channel.send(embed=embed)
            logger.info(f"Отправлено сообщение в лог-канал о {status} {content_type}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в лог-канал: {e}", exc_info=True) 