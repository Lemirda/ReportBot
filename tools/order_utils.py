import re
from datetime import datetime
from database.user import UserManager

class OrderUtils:
    """Вспомогательные функции для работы с заказами"""
    
    @staticmethod
    def extract_statics(text):
        """
        Извлекает все потенциальные статики из текста
        
        Args:
            text: Текст для извлечения статиков
            
        Returns:
            Список найденных статиков
        """
        # Извлекаем все отдельные слова как потенциальные статики
        words = re.findall(r'\b\w+\b', text)
        
        # Если текст не содержит отдельных слов, возвращаем весь текст как один статик
        if not words and text.strip():
            return [text.strip()]
            
        return words
    
    @staticmethod
    def find_users(statics, guild):
        """
        Ищет пользователей по списку статиков
        
        Args:
            statics: Список статиков для поиска
            guild: Объект сервера Discord
            
        Returns:
            Словарь {статик: пользователь или None}
        """
        user_manager = UserManager.get_instance()
        found_users = {}
        
        for static in statics:
            # Пробуем найти пользователя по точному совпадению
            users = user_manager.get_user_by_game_static(static)
            if users and len(users) > 0:
                # Попытаемся найти пользователя на сервере
                user_id = users[0]['id']
                member = guild.get_member(user_id)
                if member:
                    found_users[static] = member
                else:
                    found_users[static] = None
            else:
                found_users[static] = None
                
        return found_users
    
    @staticmethod
    def format_users_list(found_users, default_value=None):
        """
        Форматирует список найденных пользователей для отображения
        
        Args:
            found_users: Словарь {статик: пользователь или None}
            default_value: Значение по умолчанию, если пользователи не найдены
            
        Returns:
            Отформатированная строка для отображения
        """
        users_list = []
        
        if found_users:
            for static, member in found_users.items():
                if member:
                    users_list.append(f"✅ `{static}` → {member.mention}")
                else:
                    users_list.append(f"❓ `{static}` → Пользователь не найден")
            
            return "\n".join(users_list)
        else:
            return default_value if default_value else "Пользователи не найдены"
    
    @staticmethod
    def generate_order_id(user_id):
        """
        Генерирует уникальный ID заказа
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Строка с ID заказа
        """
        timestamp = int(datetime.now().timestamp())
        return f"ORD-{user_id}-{timestamp}"
    
    @staticmethod
    def get_order_price(order_type_value, custom_amount=None):
        """
        Возвращает сумму за запрос в зависимости от его типа
        
        Args:
            order_type_value: Тип заказа
            custom_amount: Пользовательская сумма (для некоторых типов заказов)
            
        Returns:
            Строка с ценой
        """
        # Проверяем, нужна ли пользовательская сумма для этого типа заказа
        custom_amount_types = ['car_repair', 'family_purchase', 'car_purchase']
        if order_type_value in custom_amount_types:
            return custom_amount if custom_amount else "Указывается пользователем"
            
        prices = {
            "conspiracy_2": "150.000-190.000",
            "conspiracy_2_activated": "150.000-190.000 + 15.000",
            "valuable_lesson": "80.000-100.000",
            "valuable_lesson_activated": "80.000-100.000 + 5.000",
            "valuable_batch": "178.000",
            "illegal_business": "174.000",
            "illegal_business_activated": "189.000",
            "grover_1": "137.000",
            "grover_1_activated": "142.000"
        }
        return prices.get(order_type_value, "Цена не указана") 