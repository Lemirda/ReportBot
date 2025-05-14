import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем ID ролей из .env файла
LEAD_ROLE_ID = int(os.getenv('LEAD_ROLE', 0))
CALLER_ROLE_ID = int(os.getenv('CALLER_ROLE', 0))
CAPTER_3_LVL_ID = int(os.getenv('CAPTER_3_LVL', 0))  # Tier 1
CAPTER_2_LVL_ID = int(os.getenv('CAPTER_2_LVL', 0))  # Tier 2
CAPTER_1_LVL_ID = int(os.getenv('CAPTER_1_LVL', 0))  # Tier 3
RAVE_ROLE_ID = int(os.getenv('RAVE_ROLE', 0))  # Роль для пинга при создании сбора

# Роли с правами на управление сборами (создание и закрытие)
CAPT_MANAGE_ROLES = []
capt_manage_roles_str = os.getenv('CAPT_MANAGE_ROLES', '')
if capt_manage_roles_str:
    CAPT_MANAGE_ROLES = [int(role_id) for role_id in capt_manage_roles_str.split(',') if role_id]

# Ранги в порядке убывания важности
RANK_HIERARCHY = [
    (1, LEAD_ROLE_ID),  # Lead
    (2, CALLER_ROLE_ID),  # Caller
    (3, CAPTER_3_LVL_ID),  # Tier 1
    (4, CAPTER_2_LVL_ID),  # Tier 2
    (5, CAPTER_1_LVL_ID),  # Tier 3
    (6, 0)  # Нет роли
]

# Словарь для получения названия ранга
RANK_NAMES = {
    1: "Lead",
    2: "Caller",
    3: "Tier 1",
    4: "Tier 2",
    5: "Tier 3",
    6: "Нет роли"
}

def get_user_rank(user):
    """
    Определяет ранг пользователя на основе его ролей
    
    Args:
        user (discord.Member): Пользователь Discord
        
    Returns:
        int: ID ранга пользователя (1 - высший, 6 - низший)
    """
    # Получаем ID ролей пользователя
    user_role_ids = [role.id for role in user.roles]
    
    # Определяем ранг пользователя (выбираем первый подходящий из иерархии)
    for rank_id, role_id in RANK_HIERARCHY:
        if role_id != 0 and role_id in user_role_ids:
            return rank_id
    
    # Если ни одна роль не подошла, возвращаем самый низкий ранг
    return RANK_HIERARCHY[-1][0]  # Ранг 6 - "Нет роли"

def get_user_rank_name(user):
    """
    Возвращает название ранга пользователя
    
    Args:
        user (discord.Member): Пользователь Discord
        
    Returns:
        str: Название ранга пользователя
    """
    rank_id = get_user_rank(user)
    return RANK_NAMES.get(rank_id, "Нет роли")

def can_manage_capt(user):
    """
    Проверяет, может ли пользователь создавать/закрывать сборы
    
    Args:
        user (discord.Member): Пользователь Discord
        
    Returns:
        bool: True если у пользователя есть права на управление сборами
    """
    # Администраторы всегда имеют доступ
    if user.guild_permissions.administrator:
        return True
        
    # Проверяем наличие ролей из списка CAPT_MANAGE_ROLES
    user_role_ids = [role.id for role in user.roles]
    for role_id in CAPT_MANAGE_ROLES:
        if role_id in user_role_ids:
            return True
            
    return False

def get_lowest_rank_user(participants):
    """Находит участника с самым низким рангом"""
    lowest_rank = 999
    lowest_rank_user = None
    
    for participant in participants:
        rank = get_user_rank(participant)
        if rank < lowest_rank:
            lowest_rank = rank
            lowest_rank_user = participant
    
    return lowest_rank_user

def sort_participants_by_rank(participants):
    """Сортирует участников по рангу (от высшего к низшему)"""
    return sorted(participants, key=lambda participant: get_user_rank(participant), reverse=True) 