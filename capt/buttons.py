import discord
from tools.logger import Logger
from tools.embed import EmbedBuilder
from capt.ranks import get_user_rank, get_lowest_rank_user, sort_participants_by_rank, can_manage_capt
from database.capt import get_instance as get_capt_db

logger = Logger.get_instance()

class JoinButton(discord.ui.Button):
    """Кнопка для присоединения к сбору"""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Присоединиться",
            custom_id="join_temp"  # Временный ID, будет обновлен
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Получаем view и данные сбора
            view = self.view
            capt_data = view.capt_data

            # Проверяем, не находится ли пользователь уже в списке
            user_id = interaction.user.id
            if any(participant.id == user_id for participant in capt_data['participants']):
                await interaction.response.send_message("Вы уже находитесь в списке участников", ephemeral=True)
                return

            # Проверяем, не находится ли пользователь в дополнительном списке
            was_moved_from_extra = False
            if any(participant.id == user_id for participant in capt_data['extra_participants']):
                # Если пользователь в доп. списке, удаляем его оттуда перед добавлением в основной
                for participant in list(capt_data['extra_participants']):
                    if participant.id == user_id:
                        capt_data['extra_participants'].remove(participant)
                        was_moved_from_extra = True
                        break

            user_rank = get_user_rank(interaction.user)

            # Если список еще не заполнен, добавляем пользователя
            if len(capt_data['participants']) < capt_data['slots']:
                capt_data['participants'].append(interaction.user)
                # Сортируем участников по рангу
                capt_data['participants'] = sort_participants_by_rank(capt_data['participants'])

                if was_moved_from_extra:
                    await interaction.response.send_message(f"Вы были перемещены из дополнительного списка в основной список", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Вы добавлены в список участников сбора '{capt_data['name']}'", ephemeral=True)
            else:
                # Список заполнен, проверяем возможность замены
                lowest_rank_user = get_lowest_rank_user(capt_data['participants'])
                lowest_rank = get_user_rank(lowest_rank_user)

                if user_rank < lowest_rank:  # Меньшее значение ранга = более высокий ранг
                    # Перемещаем участника с низшим рангом в доп. список
                    capt_data['participants'].remove(lowest_rank_user)
                    capt_data['extra_participants'].append(lowest_rank_user)

                    # Добавляем нового участника
                    capt_data['participants'].append(interaction.user)

                    # Сортируем участников по рангу
                    capt_data['participants'] = sort_participants_by_rank(capt_data['participants'])

                    await interaction.response.send_message(
                        f"Вы добавлены в основной список, участник с более низким рангом перемещен в дополнительный список",
                        ephemeral=True
                    )
                else:
                    # Добавляем в дополнительный список, если ранг ниже минимального
                    capt_data['extra_participants'].append(interaction.user)
                    await interaction.response.send_message(f"Вы добавлены в дополнительный список сбора '{capt_data['name']}'", ephemeral=True)

            # Обновляем эмбед
            embed = EmbedBuilder.create_capt_embed(capt_data)
            await interaction.message.edit(embed=embed)

            message_id = str(interaction.message.id)

            try:
                # Обновление напрямую из кнопки
                capt_db = get_capt_db()
                capt_db.save_capt(message_id, capt_data)

                # Обновление через CaptCommand (для сохранения в памяти)
                command_cog = None
                for cog in interaction.client.cogs.values():
                    if cog.__class__.__name__ == "CaptCommand":
                        command_cog = cog
                        break

                if command_cog:
                    command_cog.update_capt_data(message_id, capt_data)
            except Exception as update_error:
                logger.error(f"Ошибка при обновлении данных сбора: {update_error}", exc_info=True)

        except Exception as e:
            logger.error(f"Ошибка при присоединении к сбору: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.", ephemeral=True)

class JoinExtraButton(discord.ui.Button):
    """Кнопка для присоединения к дополнительному списку"""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Присоединиться к доп. слоту",
            custom_id="extra_temp"  # Временный ID, будет обновлен
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Получаем view и данные сбора
            view = self.view
            capt_data = view.capt_data

            # Проверяем, находится ли пользователь в основном списке
            user_id = interaction.user.id
            was_in_main_list = False

            # Проверяем, не находится ли пользователь уже в дополнительном списке
            if any(participant.id == user_id for participant in capt_data['extra_participants']):
                await interaction.response.send_message("Вы уже находитесь в дополнительном списке", ephemeral=True)
                return

            # Если пользователь в основном списке, удаляем его оттуда
            for participant in list(capt_data['participants']):
                if participant.id == user_id:
                    capt_data['participants'].remove(participant)
                    was_in_main_list = True
                    break

            # Добавляем пользователя в дополнительный список
            capt_data['extra_participants'].append(interaction.user)

            if was_in_main_list:
                await interaction.response.send_message(f"Вы были перемещены из основного списка в дополнительный список", ephemeral=True)

                # Если есть люди в доп. списке, перемещаем лучшего в основной
                if len(capt_data['participants']) < capt_data['slots'] and len(capt_data['extra_participants']) > 1:
                    # Нам нужно получить список без текущего пользователя
                    extra_without_current = [p for p in capt_data['extra_participants'] 
                                           if p.id != interaction.user.id]

                    if extra_without_current:
                        from capt.ranks import sort_participants_by_rank

                        # Сортируем и берем участника с высшим рангом
                        sorted_extra = sort_participants_by_rank(extra_without_current)
                        best_extra = sorted_extra[0]

                        # Перемещаем его в основной список
                        capt_data['extra_participants'].remove(best_extra)
                        capt_data['participants'].append(best_extra)

                        # Сортируем основной список
                        capt_data['participants'] = sort_participants_by_rank(capt_data['participants'])
            else:
                await interaction.response.send_message(f"Вы добавлены в дополнительный список сбора '{capt_data['name']}'", ephemeral=True)

            # Обновляем эмбед
            embed = EmbedBuilder.create_capt_embed(capt_data)
            await interaction.message.edit(embed=embed)

            message_id = str(interaction.message.id)

            try:
                # Обновление напрямую из кнопки
                capt_db = get_capt_db()
                capt_db.save_capt(message_id, capt_data)

                # Обновление через CaptCommand (для сохранения в памяти)
                command_cog = None
                for cog in interaction.client.cogs.values():
                    if cog.__class__.__name__ == "CaptCommand":
                        command_cog = cog
                        break

                if command_cog:
                    command_cog.update_capt_data(message_id, capt_data)
            except Exception as update_error:
                logger.error(f"Ошибка при обновлении данных сбора: {update_error}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Ошибка при присоединении к доп. списку: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.", ephemeral=True)

class LeaveButton(discord.ui.Button):
    """Кнопка для выхода из сбора"""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Покинуть",
            custom_id="leave_temp"  # Временный ID, будет обновлен
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Получаем view и данные сбора
            view = self.view
            capt_data = view.capt_data

            # Проверяем наличие пользователя в списках
            user_id = interaction.user.id
            removed_from_main = False

            # Ищем в основном списке
            for participant in capt_data['participants']:
                if participant.id == user_id:
                    capt_data['participants'].remove(participant)
                    removed_from_main = True
                    break

            # Если пользователь был в основном списке и есть люди в доп. списке, перемещаем лучшего из доп. списка в основной
            if removed_from_main and capt_data['extra_participants']:
                # Сортируем доп. список по рангу
                sorted_extra = sort_participants_by_rank(capt_data['extra_participants'])
                # Берем участника с высшим рангом из доп. списка
                best_extra = sorted_extra[0]
                # Перемещаем его в основной список
                capt_data['extra_participants'].remove(best_extra)
                capt_data['participants'].append(best_extra)
                # Сортируем основной список
                capt_data['participants'] = sort_participants_by_rank(capt_data['participants'])

                await interaction.response.send_message(
                    f"Вы покинули основной список сбора. Участник из дополнительного списка перемещен в основной.",
                    ephemeral=True
                )
            elif removed_from_main:
                await interaction.response.send_message(f"Вы покинули основной список сбора.", ephemeral=True)
            else:
                # Ищем в дополнительном списке
                removed_from_extra = False
                for participant in capt_data['extra_participants']:
                    if participant.id == user_id:
                        capt_data['extra_participants'].remove(participant)
                        removed_from_extra = True
                        break

                if removed_from_extra:
                    await interaction.response.send_message(f"Вы покинули дополнительный список сбора.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Вы не найдены в списках участников.", ephemeral=True)
                    return

            # Обновляем эмбед
            embed = EmbedBuilder.create_capt_embed(capt_data)
            await interaction.message.edit(embed=embed)

            message_id = str(interaction.message.id)

            try:
                # Обновление напрямую из кнопки
                capt_db = get_capt_db()
                capt_db.save_capt(message_id, capt_data)

                # Обновление через CaptCommand (для сохранения в памяти)
                command_cog = None
                for cog in interaction.client.cogs.values():
                    if cog.__class__.__name__ == "CaptCommand":
                        command_cog = cog
                        break

                if command_cog:
                    command_cog.update_capt_data(message_id, capt_data)
            except Exception as update_error:
                logger.error(f"Ошибка при обновлении данных сбора: {update_error}", exc_info=True)

        except Exception as e:
            logger.error(f"Ошибка при выходе из сбора: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.", ephemeral=True)

class CloseButton(discord.ui.Button):
    """Кнопка для закрытия сбора"""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Закрыть сбор",
            custom_id="close_temp"  # Временный ID, будет обновлен
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Проверяем, есть ли у пользователя права на закрытие сбора
            view = self.view
            capt_data = view.capt_data

            # Проверяем только наличие роли с правами на управление сборами
            if not can_manage_capt(interaction.user):
                await interaction.response.send_message("У вас нет прав на закрытие сбора", ephemeral=True)
                return

            # Деактивируем все кнопки
            for child in view.children:
                child.disabled = True

            # Обновляем сообщение с деактивированными кнопками
            await interaction.response.edit_message(view=view)

            message_id = str(interaction.message.id)

            try:
                # Удаление напрямую из кнопки
                capt_db = get_capt_db()
                capt_db.delete_capt(message_id)

                # Удаление через CaptCommand (для сохранения в памяти)
                command_cog = None
                for cog in interaction.client.cogs.values():
                    if cog.__class__.__name__ == "CaptCommand":
                        command_cog = cog
                        break

                if command_cog:
                    command_cog.remove_capt(message_id)
            except Exception as update_error:
                logger.error(f"Ошибка при удалении данных сбора: {update_error}", exc_info=True)

        except Exception as e:
            logger.error(f"Ошибка при закрытии сбора: {e}", exc_info=True)
            await interaction.response.send_message("Произошла ошибка. Пожалуйста, попробуйте позже.", ephemeral=True) 