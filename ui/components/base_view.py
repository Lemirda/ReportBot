import discord

class BaseView(discord.ui.View):
    """Базовый класс для всех представлений с кнопками"""

    def __init__(self, bot: discord.Client, timeout: float = None):
        """
        Инициализация базового представления

        Args:
            bot: Экземпляр бота
            timeout: Таймаут представления (None = бесконечный)
        """
        super().__init__(timeout=timeout)
        self.bot = bot
        # Сохраняем постоянное представление для работы после перезапуска
        self.bot.add_view(self)