import discord

from tools.logger import Logger
from capt.buttons import JoinButton, JoinExtraButton, LeaveButton, CloseButton

logger = Logger.get_instance()

class CaptView(discord.ui.View):
    """View с кнопками для сбора игроков"""
    
    def __init__(self, capt_data):
        super().__init__(timeout=None)
        self.capt_data = capt_data

        self.join_button = JoinButton()
        self.extra_button = JoinExtraButton()
        self.leave_button = LeaveButton()
        self.close_button = CloseButton()

        self.add_item(self.join_button)
        self.add_item(self.extra_button)
        self.add_item(self.leave_button)
        self.add_item(self.close_button)
    
    def update_button_ids(self, message_id):
        """Обновляет custom_id кнопок, добавляя ID сообщения"""
        self.join_button.custom_id = f"join_{message_id}"
        self.extra_button.custom_id = f"extra_{message_id}"
        self.leave_button.custom_id = f"leave_{message_id}"
        self.close_button.custom_id = f"close_{message_id}" 