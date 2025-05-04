import os
import logging
import datetime
import sys

from logging.handlers import RotatingFileHandler

class Logger:
    """Класс для логирования с ротацией логов"""

    def __init__(self, name="bot", log_dir="logs"):
        """
        Инициализация логгера

        Args:
            name: Имя логгера
            log_dir: Директория для хранения логов
        """
        self.name = name
        self.log_dir = log_dir

        os.makedirs(log_dir, exist_ok=True)

        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file_path = os.path.join(log_dir, f"{name}_{date_str}.log")

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        file_handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )

        console_handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.handlers = []
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.info(f"Логгер инициализирован, логи сохраняются в {self.log_file_path}")

    def info(self, message):
        """
        Логирование информационного сообщения

        Args:
            message: Сообщение для записи в лог
        """
        self.logger.info(message)

    def error(self, message, exc_info=False):
        """
        Логирование сообщения об ошибке

        Args:
            message: Сообщение для записи в лог
            exc_info: Логировать информацию об исключении
        """
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message):
        """
        Логирование предупреждения

        Args:
            message: Сообщение для записи в лог
        """
        self.logger.warning(message)

    def debug(self, message):
        """
        Логирование отладочного сообщения

        Args:
            message: Сообщение для записи в лог
        """
        self.logger.debug(message)

    def critical(self, message):
        """
        Логирование критической ошибки

        Args:
            message: Сообщение для записи в лог
        """
        self.logger.critical(message)

    @classmethod
    def get_instance(cls, name="bot", log_dir="logs"):
        """
        Получение глобального экземпляра логгера

        Args:
            name: Имя логгера
            log_dir: Директория для хранения логов

        Returns:
            Экземпляр логгера
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls(name, log_dir)

        return cls._instance