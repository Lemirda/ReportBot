import discord

from report.report_button import ReportButton
from suggestion.suggestion_button import SuggestionButton
from order.order_button import OrderButton
from afk.afk_button import AfkButton
from promotion.promotion_button import PromotionButton

from tools.logger import Logger

logger = Logger.get_instance()

class FeedbackView(discord.ui.View):
    """View с кнопками для жалоб и предложений"""

    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(ReportButton())
        self.add_item(SuggestionButton())

class OrderView(discord.ui.View):
    """View с кнопкой для размещения запросов"""

    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(OrderButton())
        
class AfkView(discord.ui.View):
    """View с кнопкой для отметки АФК"""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(AfkButton())
        
class PromotionView(discord.ui.View):
    """View с кнопкой для отправки заявки на повышение"""

    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(PromotionButton()) 