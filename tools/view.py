import discord

from report.report_button import ReportButton
from suggestion.suggestion_button import SuggestionButton
from order.order_button import OrderButton

class FeedbackView(discord.ui.View):
    """Представление с кнопками обратной связи"""

    def __init__(self, bot: discord.Client):
        super().__init__(timeout=None)
        self.bot = bot

        self.add_item(ReportButton())
        self.add_item(SuggestionButton())

class OrderView(discord.ui.View):
    """Представление с кнопкой ордера"""

    def __init__(self, bot: discord.Client):
        super().__init__(timeout=None)
        self.bot = bot

        self.add_item(OrderButton())