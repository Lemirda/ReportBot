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
    async def send_submission_notification(user, submission_type, embed):
        """
        Отправляет пользователю уведомление о создании заявки (жалобы или предложения)
        
        Args:
            user: Пользователь, отправивший заявку
            submission_type: Тип заявки ('жалоба' или 'предложение')
            embed: Эмбед с информацией о заявке
            
        Returns:
            bool: True если сообщение отправлено успешно, False в случае ошибки
        """
        content = f"Ваша заявка ({submission_type}) отправлена на рассмотрение:"
        return await NotificationManager.send_dm_notification(user, content=content, embed=embed)
    
    @staticmethod
    async def send_decision_notification(user, submission_type, decision, embed):
        """
        Отправляет пользователю уведомление о решении по заявке
        
        Args:
            user: Пользователь, отправивший заявку
            submission_type: Тип заявки ('жалоба' или 'предложение')
            decision: Решение ('одобрена' или 'отклонена')
            embed: Эмбед с информацией о решении
            
        Returns:
            bool: True если сообщение отправлено успешно, False в случае ошибки
        """
        return await NotificationManager.send_dm_notification(user, embed=embed) 