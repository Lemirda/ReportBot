import discord

from ui.components.base_view import BaseView
from report.report_button import ReportButton
from suggestion.suggestion_button import SuggestionButton

class MainView(BaseView):
    """Основное представление с кнопками для репорта и предложения"""

    def __init__(self, bot: discord.Client):
        """
        Инициализация основного представления

        Args:
            bot: Экземпляр бота
        """
        # Инициализируем базовый класс с бесконечным таймаутом
        super().__init__(bot=bot, timeout=None)

        # Добавляем кнопки
        self.add_item(ReportButton())
        self.add_item(SuggestionButton())