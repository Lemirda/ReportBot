import discord

from abc import ABC, abstractmethod

class BaseButton(discord.ui.Button, ABC):
    """Базовый класс для всех кнопок"""

    def __init__(self, label: str, style: discord.ButtonStyle, custom_id: str):
        """
        Инициализация базовой кнопки

        Args:
            label: Текст кнопки
            style: Стиль кнопки
            custom_id: Уникальный идентификатор кнопки (для сохранения состояния)
        """
        super().__init__(label=label, style=style, custom_id=custom_id)

    @abstractmethod
    async def callback(self, interaction: discord.Interaction):
        """
        Абстрактный метод обработки нажатия на кнопку

        Args:
            interaction: Объект взаимодействия с пользователем
        """
        pass