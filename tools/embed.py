import discord
from datetime import datetime
from tools.order_utils import OrderUtils

class EmbedBuilder:
    """Класс для создания всех эмбедов в приложении"""
    
    @staticmethod
    def create_report_embed(user, report_data):
        """Создает эмбед для жалобы"""
        embed = discord.Embed(title="Жалоба", color=discord.Color.red())
        embed.add_field(name="От кого", value=user.mention, inline=False)
        embed.add_field(name="На кого", value=report_data.get('target', 'Не указано'), inline=False)
        embed.add_field(name="Описание", value=report_data.get('description', 'Не указано'), inline=False)
        embed.add_field(name="Доказательства", value=report_data.get('evidence', 'Не указано'), inline=False)
        return embed
    
    @staticmethod
    def create_suggestion_embed(user, suggestion_data):
        """Создает эмбед для предложения"""
        embed = discord.Embed(title="Предложение", color=discord.Color.green())
        embed.add_field(name="От кого", value=user.mention, inline=False)
        embed.add_field(name="Описание", value=suggestion_data.get('description', 'Не указано'), inline=False)
        return embed
    
    @staticmethod
    def create_order_embed(user, order_data, users_value=None, guild=None):
        """Создает эмбед для запроса"""
        order_type_label = order_data.get('order_type', 'Не указано')
        order_type_value = order_data.get('order_type_value', 'Не указано')
        
        # Создаем embed
        embed = discord.Embed(
            title=f":identification_card: Запрос: {order_type_label}", 
            color=0x3498db
        )
        
        # Текущая дата и время
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Поле информации о заказчике
        embed.add_field(
            name="👤 Заказчик",
            value=f"{user.mention}\nID: `{user.id}`",
            inline=False
        )
        
        # Получаем пользовательскую сумму, если она указана
        custom_amount = order_data.get('amount')
        
        # Поле с типом и ценой
        embed.add_field(
            name="💰 Информация",
            value=f"**Тип:** {order_type_label}\n**Стоимость:** {OrderUtils.get_order_price(order_type_value, custom_amount)}",
            inline=False
        )
        
        # Поле с пользователями по статикам
        if users_value:
            embed.add_field(
                name="🔍 Пользователи по статикам",
                value=users_value,
                inline=False
            )
        
        # Доказательства с форматированием
        evidence = order_data.get('evidence', 'Не указано')
        embed.add_field(
            name="📷 Доказательства",
            value=f"```{evidence}```",
            inline=False
        )
        
        # Устанавливаем футер с ID заказа и временем
        order_id = OrderUtils.generate_order_id(user.id)
        embed.set_footer(text=f"ID заказа: {order_id} • {current_time}")
        
        # Добавляем уменьшенный аватар пользователя
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        return embed
    
    @staticmethod
    def create_feedback_embed():
        """Создает эмбед для канала обратной связи"""
        embed = discord.Embed(
            title="Обратная связь",
            description="Используйте кнопки ниже, чтобы отправить жалобу или предложение по улучшению сервера.",
            color=discord.Color.blue()
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1368531461929701546/1369951883141189782/Grand_Theft_Auto_V_Screenshot_2025.png?ex=681dba9d&is=681c691d&hm=7dde680c13aba25844026d45cc0049f2c81eac69a5334a0f403c12d0de39fcec&")

        embed.add_field(
            name="🚨 Жалоба", 
            value="Нажмите кнопку 'Жалоба', чтобы сообщить о нарушении правил другим пользователем.", 
            inline=False
        )

        embed.add_field(
            name="💡 Предложение",
            value="Нажмите кнопку 'Предложение', чтобы предложить улучшение или новую функцию для сервера.",
            inline=False
        )
        
        return embed
    
    @staticmethod
    def create_order_button_embed():
        """Создает эмбед для канала запросов"""
        embed = discord.Embed(
            title="Запросы",
            description="Используйте кнопку ниже, чтобы разместить запрос.",
            color=discord.Color.blue()
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1368531461929701546/1369951883141189782/Grand_Theft_Auto_V_Screenshot_2025.png?ex=681dba9d&is=681c691d&hm=7dde680c13aba25844026d45cc0049f2c81eac69a5334a0f403c12d0de39fcec&")
        
        embed.add_field(
            name="📋 Запрос",
            value="Нажмите кнопку 'Разместить запрос', чтобы создать заявку на выполнение миссии.",
            inline=False
        )
        
        return embed
    
    @staticmethod
    def create_decision_embed(content_type, is_approved, moderator, original_embed=None, reason=None):
        """Создает эмбед для уведомления о решении"""
        # Определяем правильное склонение для статуса
        if is_approved:
            status = 'одобрен' if content_type == 'запрос' else ('одобрено' if content_type in ['предложение', 'повышение'] else 'одобрена')
            color = discord.Color.green()
        else:
            status = 'отклонен' if content_type == 'запрос' else ('отклонено' if content_type in ['предложение', 'повышение'] else 'отклонена')
            color = discord.Color.red()
        
        # Определяем правильное склонение для местоимения
        pronoun = '' if content_type == 'запрос' else ('е' if content_type in ['предложение', 'повышение'] else 'а')
        
        # Определяем правильное склонение глагола "было/был/была"
        verb = 'был' if content_type == 'запрос' else ('было' if content_type in ['предложение', 'повышение'] else 'была')
        
        embed = discord.Embed(
            title=f"{content_type.capitalize()} {status}",
            description=f"Ваш{pronoun} {content_type} {verb} {status}.\nМодератор: {moderator.mention}",
            color=color
        )
        
        # Добавляем поля из оригинального эмбеда, если он предоставлен
        if original_embed:
            for field in original_embed.fields:
                if field.name not in ["От кого", "Статус"]:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
        
        # Добавляем причину отказа, если она предоставлена
        if reason and not is_approved:
            embed.add_field(name="Причина отказа", value=reason, inline=False)
        
        # Добавляем дату
        current_date = datetime.now().strftime("%d.%m.%Y")
        embed.set_footer(text=f"{current_date}")
        
        return embed
    
    @staticmethod
    def create_afk_embed(afk_data):
        """Создает эмбед с информацией об АФК пользователя
        
        Args:
            afk_data: Словарь с данными об АФК
                - user: Пользователь
                - start_timestamp: Временная метка начала АФК
                - end_timestamp: Временная метка окончания АФК
                - reason: Причина АФК
        """
        user = afk_data.get('user')
        start_timestamp = afk_data.get('start_timestamp')
        end_timestamp = afk_data.get('end_timestamp')
        reason = afk_data.get('reason', 'Не указана')
        
        embed = discord.Embed(
            title=f"⏰ АФК: {user.display_name}", 
            color=0xFF9900
        )

        embed.add_field(
            name="👤 Пользователь",
            value=f"{user.mention}\nID: `{user.id}`",
            inline=False
        )

        embed.add_field(
            name="⏱️ Время",
            value=f"С <t:{start_timestamp}:t> до <t:{end_timestamp}:t>",
            inline=False
        )

        embed.add_field(
            name="📝 Причина",
            value=f"```{reason}```",
            inline=False
        )

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        return embed
    
    @staticmethod
    def create_afk_button_embed():
        """Создает эмбед для канала отметки АФК"""
        embed = discord.Embed(
            title="Отметка AFK",
            description="Используйте кнопку ниже, чтобы отметиться как AFK (отсутствующий).",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="⏰ Отсутствие",
            value="Нажмите кнопку 'Отметится', чтобы сообщить о вашем отсутствии и его причине.",
            inline=False
        )

        embed.set_image(url="https://cdn.discordapp.com/attachments/1368531461929701546/1369951883141189782/Grand_Theft_Auto_V_Screenshot_2025.png?ex=681dba9d&is=681c691d&hm=7dde680c13aba25844026d45cc0049f2c81eac69a5334a0f403c12d0de39fcec&")
        
        return embed
    
    @staticmethod
    def create_promotion_button_embed():
        """Создает эмбед для канала повышений"""
        embed = discord.Embed(
            title="Повышение ранга",
            description="Используйте кнопку ниже, чтобы подать заявку на повышение ранга.",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="⬆️ Повышение",
            value="Нажмите кнопку 'Повышение', чтобы подать заявку на повышение вашего ранга.",
            inline=False
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/1368531461929701546/1369951883141189782/Grand_Theft_Auto_V_Screenshot_2025.png?ex=681dba9d&is=681c691d&hm=7dde680c13aba25844026d45cc0049f2c81eac69a5334a0f403c12d0de39fcec&")
        
        return embed
    
    @staticmethod
    def create_promotion_embed(user, promotion_data):
        """Создает эмбед с информацией о заявке на повышение
        
        Args:
            user: Пользователь, отправивший заявку
            promotion_data: Словарь с данными о повышении
                - current_rank: Текущий ранг
                - next_rank: Следующий ранг
                - missions: МП, в которых участвовал
                - links: Ссылки на откаты
                - rules: Ознакомлен с правилами
                - days: Количество дней в фаме
                - evidence: Доказательства
        """
        current_rank = promotion_data.get('current_rank', 0)
        next_rank = promotion_data.get('next_rank', 0)
        
        embed = discord.Embed(
            title=f"⬆️ Заявка на повышение", 
            color=0x9B59B6
        )
        
        # Информация о пользователе и повышении
        embed.add_field(
            name="👤 Пользователь",
            value=f"{user.mention} с {current_rank} ранга на {next_rank} ранг",
            inline=False
        )
        
        # Информация о миссиях
        embed.add_field(
            name="🎯 МП в которых участвовал",
            value=f"```{promotion_data.get('missions', 'Не указано')}```",
            inline=False
        )
        
        # Ссылки на откаты
        embed.add_field(
            name="🔗 Ссылка на откаты",
            value=f"```{promotion_data.get('links', 'Не указано')}```",
            inline=False
        )
        
        # Ознакомление с правилами
        embed.add_field(
            name="📜 Ознакомлены ли вы с правилами?",
            value=f"```{promotion_data.get('rules', 'Не указано')}```",
            inline=False
        )
        
        # Дни в фаме
        embed.add_field(
            name="📅 Сколько дней в фаме?",
            value=f"```{promotion_data.get('days', 'Не указано')}```",
            inline=False
        )
        
        # Доказательства
        embed.add_field(
            name="📷 Доказательства",
            value=f"```{promotion_data.get('evidence', 'Не указано')}```",
            inline=False
        )
        
        # Если у пользователя есть аватар, добавляем его
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        # Добавляем текущую дату в футер
        embed.set_footer(text=f"Заявка на повышение • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        return embed 