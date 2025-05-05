import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

from tools.message_sender import MessageSender
from tools.logger import Logger
from tools.reaction_utils import handle_reaction_button

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

    try:
        channel = bot.get_channel(MAIN_CHANNEL_ID)

        if channel:
            message_sender = MessageSender(bot)
            await message_sender.send_report_embed(channel)
        else:
            logger.warning(f"Канал с ID {MAIN_CHANNEL_ID} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}", exc_info=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Обработчик взаимодействий с ботом"""

    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")

        try:
            if custom_id.startswith("approve_") or custom_id.startswith("reject_"):
                await handle_reaction_button(bot, interaction)
                return

        except Exception as e:
            logger.error(f"Ошибка при обработке взаимодействия с кнопкой {custom_id}: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка при обработке вашего действия", ephemeral=True)
            return

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Не удалось запустить бота: {e}", exc_info=True) 