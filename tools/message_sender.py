import discord
from tools.logger import Logger
from tools.view import FeedbackView, OrderView, AfkView, PromotionView
from tools.embed import EmbedBuilder
from group.view import GroupView

logger = Logger.get_instance()

class MessageSender:
    """Класс для отправки сообщений и эмбедов в каналы Discord"""

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def clear_channel(self, channel: discord.TextChannel):
        """Очищает канал от сообщений"""
        try:
            if isinstance(channel, discord.TextChannel):
                async for message in channel.history(limit=None):
                    await message.delete()
                logger.info(f"Сообщения в канале {channel.name} очищены")
        except Exception as e:
            logger.error(f"Ошибка при очистке канала: {e}", exc_info=True)

    async def send_embed(self, channel: discord.abc.Messageable, embed: discord.Embed, view=None):
        """Отправляет эмбед в указанный канал с опциональным view"""
        try:
            sent_message = await channel.send(embed=embed, view=view)
            logger.info(f"Отправлено сообщение с эмбедом в канал {getattr(channel, 'name', channel.id)}")
            return sent_message
        except Exception as e:
            logger.error(f"Ошибка при отправке эмбеда: {e}", exc_info=True)
            return None

    @staticmethod
    async def send_thread_message(interaction, capt_data, message):
        """
        Отправляет сообщение в тред сбора. Если треда нет или он недоступен, не делает ничего.
        
        Args:
            interaction: Объект взаимодействия Discord или None
            capt_data: Данные о сборе
            message: Текст сообщения для отправки
        """
        if 'thread_id' in capt_data and capt_data['thread_id']:
            try:
                # Для автоматического закрытия взаимодействие может быть None
                if interaction is None:
                    # В этом случае нам нужен объект бота, но мы не можем его получить напрямую
                    # Логируем ошибку и выходим, в реальном вызове из CaptCommand бот доступен
                    logger.warning(f"Не удалось отправить сообщение в тред: объект interaction не предоставлен")
                    return
                else:
                    # Пытаемся получить тред
                    thread = interaction.channel.get_thread(capt_data['thread_id'])
                    if thread:
                        await thread.send(message)
                        return
                
                logger.warning(f"Тред {capt_data['thread_id']} не найден для сбора {capt_data.get('name', 'Без имени')}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в тред: {e}", exc_info=True)

    async def send_report_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопками обратной связи"""
        # Сначала очищаем канал, если это текстовый канал
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        # Создаем эмбед с помощью EmbedBuilder
        embed = EmbedBuilder.create_feedback_embed()

        # Создаем view и отправляем эмбед
        view = FeedbackView(self.bot)
        return await self.send_embed(channel, embed, view)

    async def send_order_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопкой запроса"""
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        # Создаем эмбед с помощью EmbedBuilder
        embed = EmbedBuilder.create_order_button_embed()

        view = OrderView(self.bot)
        return await self.send_embed(channel, embed, view)

    async def send_afk_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопкой отметки АФК"""
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        embed = EmbedBuilder.create_afk_button_embed()

        view = AfkView()
        return await self.send_embed(channel, embed, view)

    async def send_promotion_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопкой повышения"""
        if isinstance(channel, discord.TextChannel):
            await self.clear_channel(channel)

        # Создаем эмбед для повышения
        embed = EmbedBuilder.create_promotion_button_embed()

        view = PromotionView(self.bot)
        return await self.send_embed(channel, embed, view)

    async def send_group_embed(self, channel: discord.abc.Messageable):
        """Отправляет эмбед с кнопками для создания групп"""
        # Проверяем, есть ли уже закрепленные сообщения с кнопками
        if isinstance(channel, discord.TextChannel):
            pins = await channel.pins()
            for pin in pins:
                if pin.author == self.bot.user and len(pin.components) > 0:
                    logger.info(f"Сообщение с кнопками для групп уже существует (ID: {pin.id})")
                    return pin
        
        # Создаем эмбед
        embed = discord.Embed(
            title="Создание группы",
            description="Используйте кнопки ниже для создания группы определенного типа.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Инструкция",
            value="1. Выберите тип группы\n2. Укажите время проведения\n3. Бот отправит 5 сообщений с тегом @Rave",
            inline=False
        )
        
        # Создаем view с кнопками
        view = GroupView()
        
        # Отправляем сообщение
        message = await self.send_embed(channel, embed, view)
        
        # Закрепляем сообщение
        if message and isinstance(channel, discord.TextChannel):
            try:
                await message.pin()
                logger.info(f"Сообщение с кнопками для групп создано и закреплено (ID: {message.id})")
            except discord.HTTPException as e:
                logger.warning(f"Не удалось закрепить сообщение с кнопками для групп: {e}")
                logger.info(f"Сообщение с кнопками для групп создано (ID: {message.id}), но не закреплено")
        
        return message 