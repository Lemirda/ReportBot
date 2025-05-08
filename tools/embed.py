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
            status = 'одобрен' if content_type == 'запрос' else ('одобрено' if content_type == 'предложение' else 'одобрена')
            color = discord.Color.green()
        else:
            status = 'отклонен' if content_type == 'запрос' else ('отклонено' if content_type == 'предложение' else 'отклонена')
            color = discord.Color.red()
        
        # Определяем правильное склонение для местоимения
        pronoun = '' if content_type == 'запрос' else ('е' if content_type == 'предложение' else 'а')
        
        embed = discord.Embed(
            title=f"{content_type.capitalize()} {status}",
            description=f"Ваш{pronoun} {content_type} был{pronoun} {status}.\nМодератор: {moderator.mention}",
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