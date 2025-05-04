import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

from ui.embed_message import EmbedMessageHandler
from utils.logger import Logger
from utils.reaction_utils import handle_reaction_button

logger = Logger.get_instance()

load_dotenv()

TOKEN = os.getenv('TOKEN')
MAIN_CHANNEL_ID = int(os.getenv('MAIN_CHANNEL'))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user} запущен и готов к работе!')

    for guild in bot.guilds:
        logger.info(f"Сервер: {guild.name} (ID: {guild.id})")
        logger.info(f"Роли на сервере:")
        for role in guild.roles:
            logger.info(f"  - {role.name} (ID: {role.id})")

    await bot.tree.sync()

    try:
        channel = bot.get_channel(MAIN_CHANNEL_ID)

        if channel:
            embed_handler = EmbedMessageHandler(bot)
            await embed_handler.send_main_embed(channel)
        else:
            logger.warning(f"Канал с ID {MAIN_CHANNEL_ID} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}", exc_info=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Обработчик взаимодействий с ботом"""

    if interaction.type == discord.InteractionType.component:
        # Получаем ID кнопки
        custom_id = interaction.data.get("custom_id", "")

        try:
            # Если это кнопка одобрения или отклонения
            if custom_id.startswith("approve_") or custom_id.startswith("reject_"):
                await handle_reaction_button(bot, interaction)
                return

        except Exception as e:
            logger.error(f"Ошибка при обработке взаимодействия с кнопкой {custom_id}: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка при обработке вашего действия", ephemeral=True)
            return

if __name__ == "__main__":
    logger.info("Запуск бота...")

    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Не удалось запустить бота: {e}", exc_info=True) 