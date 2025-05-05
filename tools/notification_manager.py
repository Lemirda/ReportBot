import discord
from tools.logger import Logger

logger = Logger.get_instance()

class NotificationManager:
    """Менеджер для отправки уведомлений пользователям"""

    @staticmethod
    async def send_dm_notification(user, content=None, embed=None):
        """
        Отправляет пользователю сообщение в личные сообщения (DM)
        
        Args:
            user: Пользователь, которому нужно отправить сообщение
            content: Текст сообщения (опционально)
            embed: Эмбед для отображения (опционально)
            
        Returns:
            bool: True если сообщение отправлено успешно, False в случае ошибки
        """
        try:
            await user.send(content=content, embed=embed)
            logger.info(f"Отправлено уведомление в ЛС пользователю {user.name} ({user.id})")
            return True
        except discord.Forbidden:
            logger.warning(f"Невозможно отправить ЛС пользователю {user.name} ({user.id}) - доступ запрещен")
            return False
        except Exception as e:
            logger.error(f"Ошибка при отправке ЛС пользователю {user.name} ({user.id}): {e}", exc_info=True)
            return False
            
    @staticmethod
    async def send_submission_notification(user, embed):
        """Отправляет пользователю уведомление о создании заявки (жалобы или предложения)"""
        return await NotificationManager.send_dm_notification(user, embed=embed)
    
    @staticmethod
    async def send_decision_notification(user, embed):
        """Отправляет пользователю уведомление о решении по заявке"""
        return await NotificationManager.send_dm_notification(user, embed=embed) 