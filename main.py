import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

from tools.message_sender import MessageSender
from tools.logger import Logger
from tools.reaction_handlers import handle_reaction_button
from database.user import UserManager

logger = Logger.get_instance()

load_dotenv()

TOKEN = os.getenv('TOKEN')
MAIN_CHANNEL_ID = int(os.getenv('MAIN_CHANNEL'))
ORDER_CHANNEL = int(os.getenv('ORDER_CHANNEL'))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user} запущен и готов к работе!')

    try:
        # Синхронизация базы данных пользователей
        for guild in bot.guilds:
            user_manager = UserManager.get_instance()
            added, updated = user_manager.sync_guild_members(guild)
            logger.info(f"Синхронизация пользователей сервера {guild.name}: добавлено {added}, обновлено {updated}")
            
            # Вывод всех пользователей и их статиков для тестирования
            #all_users = user_manager.get_all_users()
            #logger.info(f"Всего пользователей в базе: {len(all_users)}")
            #logger.info("=== СПИСОК ПОЛЬЗОВАТЕЛЕЙ И ИХ СТАТИКОВ ===")
            #for user in all_users:
                #user_display_name = user['display_name']
                #user_static = user['game_static'] if user['game_static'] else "Статик не определен"
                #logger.info(f"Пользователь: {user_display_name} | Статик: {user_static}")
            #logger.info("=== КОНЕЦ СПИСКА ===")

        channel_report = bot.get_channel(MAIN_CHANNEL_ID)
        channel_order = bot.get_channel(ORDER_CHANNEL)

        message_sender = MessageSender(bot)
        await message_sender.send_report_embed(channel_report)
        await message_sender.send_order_embed(channel_order)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}", exc_info=True)

@bot.event
async def on_member_join(member):
    """Обработчик события входа пользователя на сервер"""
    try:
        user_manager = UserManager.get_instance()
        user_manager.update_user(member.id, member.display_name)
        logger.info(f"Пользователь {member.display_name} (ID: {member.id}) присоединился к серверу")
    except Exception as e:
        logger.error(f"Ошибка при обработке входа пользователя: {e}", exc_info=True)

@bot.event
async def on_member_remove(member):
    """Обработчик события выхода пользователя с сервера"""
    try:
        # Удаляем пользователя из базы данных
        user_manager = UserManager.get_instance()
        deleted = user_manager.delete_user(member.id)
        if deleted:
            logger.info(f"Пользователь {member.display_name} (ID: {member.id}) удален из базы данных при выходе с сервера")
        else:
            logger.warning(f"Не удалось удалить пользователя {member.display_name} (ID: {member.id}) из базы данных")
        
        logger.info(f"Пользователь {member.display_name} (ID: {member.id}) покинул сервер")
    except Exception as e:
        logger.error(f"Ошибка при обработке выхода пользователя: {e}", exc_info=True)

@bot.event
async def on_member_update(before, after):
    """Обработчик события обновления участника сервера"""
    try:
        # Проверяем, изменилось ли отображаемое имя
        if before.display_name != after.display_name:
            user_manager = UserManager.get_instance()
            user_manager.update_user(after.id, after.display_name)
            logger.info(f"Пользователь изменил отображаемое имя: {before.display_name} -> {after.display_name} (ID: {after.id})")
    except Exception as e:
        logger.error(f"Ошибка при обработке обновления участника сервера: {e}", exc_info=True)

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