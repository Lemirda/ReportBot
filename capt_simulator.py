import tkinter as tk
import random
import time
import threading
import queue
from enum import Enum
from typing import List, Dict, Any

class Rank(Enum):
    """Ранги участников"""
    LEADER = 1
    CAPTAIN_1 = 2
    CAPTAIN_2 = 3
    MEMBER = 4
    NO_ROLE = 5

class Action(Enum):
    """Возможные действия участников"""
    JOIN = 1
    JOIN_EXTRA = 2
    LEAVE = 3

class Participant:
    """Класс участника сбора"""
    def __init__(self, id: int, name: str, rank: Rank):
        self.id = id
        self.name = name
        self.rank = rank
    
    def __str__(self) -> str:
        if self.rank == Rank.LEADER:
            return f"{self.name} [LEADER]"
        elif self.rank == Rank.CAPTAIN_1:
            return f"{self.name} [CAPTAIN 1 LVL]"
        elif self.rank == Rank.CAPTAIN_2:
            return f"{self.name} [CAPTAIN 2 LVL]"
        elif self.rank == Rank.MEMBER:
            return f"{self.name} [MEMBER]"
        else:
            return f"{self.name} [Нет роли]"

class CaptSimulator:
    """Симулятор сбора участников"""
    def __init__(self, slots: int):
        self.slots = slots
        self.name = "Тестовый сбор"
        self.participants: List[Participant] = []
        self.extra_participants: List[Participant] = []
        self.next_id = 1
        
        # Для передачи информации между окнами
        self.update_queue = queue.Queue()
        self.main_logs = []
    
    def sort_participants(self):
        """Сортировка участников по рангу"""
        self.participants.sort(key=lambda p: p.rank.value)
    
    def get_lowest_rank_user(self):
        """Получение участника с самым низким рангом"""
        if not self.participants:
            return None
        return max(self.participants, key=lambda p: p.rank.value)
    
    def get_highest_rank_from_extra(self):
        """Получение участника с самым высоким рангом из доп. списка"""
        if not self.extra_participants:
            return None
        return min(self.extra_participants, key=lambda p: p.rank.value)
    
    def join(self, participant: Participant) -> str:
        """Присоединиться к сбору"""
        # Проверка, не находится ли уже участник в списках
        if any(p.id == participant.id for p in self.participants):
            return "Участник уже в основном списке"
        
        was_moved_from_extra = False
        # Удаляем из доп. списка, если он там есть
        for p in list(self.extra_participants):
            if p.id == participant.id:
                self.extra_participants.remove(p)
                was_moved_from_extra = True
                break
        
        # Если есть свободное место, добавляем
        if len(self.participants) < self.slots:
            self.participants.append(participant)
            self.sort_participants()
            
            if was_moved_from_extra:
                return "Перемещен из доп. списка в основной"
            return "Добавлен в основной список"
        else:
            # Список заполнен, проверим возможность замены
            lowest_rank_user = self.get_lowest_rank_user()
            
            if not lowest_rank_user or participant.rank.value < lowest_rank_user.rank.value:
                # Перемещаем участника с низшим рангом в доп. список
                if lowest_rank_user:
                    self.participants.remove(lowest_rank_user)
                    self.extra_participants.append(lowest_rank_user)
                
                # Добавляем нового участника
                self.participants.append(participant)
                self.sort_participants()
                
                return "Добавлен в основной список, участник с низким рангом перемещен в доп. список"
            else:
                # Добавляем в доп. список
                self.extra_participants.append(participant)
                return "Добавлен в дополнительный список"
    
    def join_extra(self, participant: Participant) -> str:
        """Присоединиться к доп. списку"""
        # Проверка, не находится ли уже участник в доп. списке
        if any(p.id == participant.id for p in self.extra_participants):
            return "Участник уже в доп. списке"
        
        was_in_main = False
        # Удаляем из основного списка, если он там есть
        for p in list(self.participants):
            if p.id == participant.id:
                self.participants.remove(p)
                was_in_main = True
                break
        
        # Добавляем в доп. список
        self.extra_participants.append(participant)
        
        if was_in_main:
            return "Перемещен из основного списка в доп. список"
        return "Добавлен в доп. список"
    
    def leave(self, participant: Participant) -> str:
        """Покинуть сбор"""
        # Ищем в основном списке
        for p in list(self.participants):
            if p.id == participant.id:
                self.participants.remove(p)
                return "Покинул основной список"
        
        # Ищем в доп. списке
        for p in list(self.extra_participants):
            if p.id == participant.id:
                self.extra_participants.remove(p)
                return "Покинул доп. список"
        
        return "Участник не найден в списках"
    
    def generate_random_participant(self) -> Participant:
        """Генерация случайного участника"""
        names = ["Алексей", "Сергей", "Иван", "Дмитрий", "Михаил", "Андрей", "Николай", 
                "Максим", "Владимир", "Александр", "Юрий", "Василий", "Виктор", 
                "Игорь", "Олег", "Павел", "Петр", "Роман", "Станислав", "Фёдор"]
        
        last_names = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", 
                      "Соколов", "Михайлов", "Новиков", "Федоров", "Морозов", "Волков"]
        
        name = f"{random.choice(names)} {random.choice(last_names)}"
        rank = random.choice(list(Rank))
        
        participant = Participant(self.next_id, name, rank)
        self.next_id += 1
        
        return participant

# Класс для главного окна сбора
class MainWindow(tk.Tk):
    def __init__(self, simulator: CaptSimulator):
        super().__init__()
        self.simulator = simulator
        self.title("Основное окно - Состояние сбора")
        self.geometry("600x600")
        
        # Основная рамка
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = tk.Label(main_frame, text=f"Сбор: {simulator.name} (Слотов: {simulator.slots})", 
                             font=("Arial", 14, "bold"))
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Основной список
        main_list_label = tk.Label(main_frame, text="Основной список:", font=("Arial", 12, "underline"))
        main_list_label.pack(anchor="w")
        
        # Фрейм для списка участников
        self.main_list_frame = tk.Frame(main_frame)
        self.main_list_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Доп. список
        extra_list_label = tk.Label(main_frame, text="Дополнительный список:", font=("Arial", 12, "underline"))
        extra_list_label.pack(anchor="w")
        
        # Фрейм для доп. списка
        self.extra_list_frame = tk.Frame(main_frame)
        self.extra_list_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Лог действий
        log_label = tk.Label(main_frame, text="Лог действий:", font=("Arial", 12, "underline"))
        log_label.pack(anchor="w")
        
        # Текстовое поле для лога
        self.log_text = tk.Text(main_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Обновляем UI каждые 100 мс
        self.after(100, self.update_ui)
    
    def update_ui(self):
        # Обновляем основной список
        for widget in self.main_list_frame.winfo_children():
            widget.destroy()
        
        for i, participant in enumerate(self.simulator.participants):
            tk.Label(self.main_list_frame, text=f"{i+1}. {participant}").pack(anchor="w")
        
        # Заполняем пустые слоты
        for i in range(len(self.simulator.participants), self.simulator.slots):
            tk.Label(self.main_list_frame, text=f"{i+1}. [Пусто]").pack(anchor="w")
        
        # Обновляем доп. список
        for widget in self.extra_list_frame.winfo_children():
            widget.destroy()
        
        if self.simulator.extra_participants:
            for i, participant in enumerate(self.simulator.extra_participants):
                tk.Label(self.extra_list_frame, text=f"{i+1}. {participant}").pack(anchor="w")
        else:
            tk.Label(self.extra_list_frame, text="[Пусто]").pack(anchor="w")
        
        # Обновляем лог
        self.log_text.delete(1.0, tk.END)
        for log in self.simulator.main_logs:
            self.log_text.insert(tk.END, log + "\n")
        self.log_text.see(tk.END)  # Прокрутка до конца
        
        # Планируем следующее обновление
        self.after(100, self.update_ui)

# Класс для окна управления участником
class ParticipantControlWindow(tk.Tk):
    def __init__(self, simulator: CaptSimulator, title="Управление участником"):
        super().__init__()
        self.simulator = simulator
        self.title(title)
        self.geometry("400x550")
        self.participant = None
        
        # Основная рамка
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Фрейм для информации об участнике
        self.info_frame = tk.Frame(main_frame)
        self.info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Заголовок и кнопка генерации
        header_frame = tk.Frame(self.info_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.name_label = tk.Label(header_frame, text="Нет активного участника", font=("Arial", 14, "bold"))
        self.name_label.pack(side=tk.LEFT)
        
        generate_btn = tk.Button(header_frame, text="Сгенерировать участника", command=self.generate_new_participant)
        generate_btn.pack(side=tk.RIGHT)
        
        # Информация об участнике
        self.rank_label = tk.Label(self.info_frame, text="")
        self.rank_label.pack(anchor="w")
        
        self.id_label = tk.Label(self.info_frame, text="")
        self.id_label.pack(anchor="w")
        
        # Статус участника
        self.status_label = tk.Label(self.info_frame, text="Статус: не в сборе", font=("Arial", 12))
        self.status_label.pack(anchor="w", pady=(10, 0))
        
        # Фрейм с кнопками действий
        actions_frame = tk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=10)
        
        # Кнопки действий
        self.join_btn = tk.Button(actions_frame, text="Присоединиться", 
                                 command=lambda: self.perform_action(Action.JOIN),
                                 width=15, height=2, bg="#90EE90")
        self.join_btn.pack(side=tk.LEFT, padx=5)
        
        self.join_extra_btn = tk.Button(actions_frame, text="В доп. список", 
                                       command=lambda: self.perform_action(Action.JOIN_EXTRA),
                                       width=15, height=2, bg="#ADD8E6")
        self.join_extra_btn.pack(side=tk.LEFT, padx=5)
        
        self.leave_btn = tk.Button(actions_frame, text="Покинуть", 
                                  command=lambda: self.perform_action(Action.LEAVE),
                                  width=15, height=2, bg="#FFA07A")
        self.leave_btn.pack(side=tk.LEFT, padx=5)
        
        # Лог действий
        log_label = tk.Label(main_frame, text="Лог действий:", font=("Arial", 12, "underline"))
        log_label.pack(anchor="w", pady=(10, 0))
        
        # Текстовое поле для лога
        self.log_text = tk.Text(main_frame, height=20, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Начальное состояние кнопок
        self.update_buttons_state()
        
        # Список логов действий
        self.actions_log = []
    
    def generate_new_participant(self):
        """Генерация нового случайного участника"""
        self.participant = self.simulator.generate_random_participant()
        
        # Обновляем информацию
        self.name_label.config(text=self.participant.name)
        
        role_text = ""
        if self.participant.rank == Rank.LEADER:
            role_text = "Роль: LEADER"
        elif self.participant.rank == Rank.CAPTAIN_1:
            role_text = "Роль: CAPTAIN 1 LVL"
        elif self.participant.rank == Rank.CAPTAIN_2:
            role_text = "Роль: CAPTAIN 2 LVL" 
        elif self.participant.rank == Rank.MEMBER:
            role_text = "Роль: MEMBER"
        else:
            role_text = "Роль: Нет роли"
            
        self.rank_label.config(text=role_text)
        self.id_label.config(text=f"ID: {self.participant.id}")
        
        # Добавляем в лог
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Сгенерирован новый участник: {self.participant.name} [{self.participant.rank.name}]"
        self.add_to_log(log_entry)
        
        # Обновляем состояние кнопок
        self.update_buttons_state()
    
    def perform_action(self, action: Action):
        """Выполнить действие"""
        if not self.participant:
            return
        
        result = ""
        
        if action == Action.JOIN:
            result = self.simulator.join(self.participant)
            log_msg = f"Присоединение: {result}"
        elif action == Action.JOIN_EXTRA:
            result = self.simulator.join_extra(self.participant)
            log_msg = f"Вход в доп. список: {result}"
        elif action == Action.LEAVE:
            result = self.simulator.leave(self.participant)
            log_msg = f"Выход: {result}"
        
        # Добавляем действие в логи
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {log_msg}"
        
        self.add_to_log(log_entry)
        self.simulator.main_logs.append(f"[{timestamp}] {self.participant.name}: {log_msg}")
        
        # Обновляем состояние кнопок
        self.update_buttons_state()
    
    def update_buttons_state(self):
        """Обновление состояния кнопок в зависимости от текущего состояния участника"""
        if not self.participant:
            self.join_btn.config(state=tk.DISABLED)
            self.join_extra_btn.config(state=tk.DISABLED)
            self.leave_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Статус: нет активного участника")
            return
        
        # Проверяем, где находится участник
        in_main = any(p.id == self.participant.id for p in self.simulator.participants)
        in_extra = any(p.id == self.participant.id for p in self.simulator.extra_participants)
        
        if in_main:
            self.status_label.config(text="Статус: в основном списке")
            self.join_btn.config(state=tk.DISABLED)
            self.join_extra_btn.config(state=tk.NORMAL)
            self.leave_btn.config(state=tk.NORMAL)
        elif in_extra:
            self.status_label.config(text="Статус: в дополнительном списке")
            self.join_btn.config(state=tk.NORMAL)
            self.join_extra_btn.config(state=tk.DISABLED)
            self.leave_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Статус: не в сборе")
            self.join_btn.config(state=tk.NORMAL)
            self.join_extra_btn.config(state=tk.NORMAL)
            self.leave_btn.config(state=tk.DISABLED)
    
    def add_to_log(self, log_entry: str):
        """Добавление записи в лог"""
        self.actions_log.append(log_entry)
        self.log_text.delete(1.0, tk.END)
        for log in self.actions_log:
            self.log_text.insert(tk.END, log + "\n")
        self.log_text.see(tk.END)  # Прокрутка до конца
        
def main():
    # Получаем количество слотов
    slots_window = tk.Tk()
    slots_window.title("Настройка сбора")
    slots_window.geometry("400x150")
    
    tk.Label(slots_window, text="Введите количество слотов (1-10):", font=("Arial", 12)).pack(pady=10)
    
    slots_var = tk.StringVar()
    slots_entry = tk.Entry(slots_window, textvariable=slots_var, width=10, font=("Arial", 12))
    slots_entry.pack(pady=10)
    slots_entry.focus_set()
    
    def start_simulation():
        slots_str = slots_var.get()
        try:
            slots = int(slots_str)
            if 1 <= slots <= 10:
                slots_window.destroy()
                
                # Создаем симулятор
                simulator = CaptSimulator(slots)
                
                # Создаем окна
                main_window = MainWindow(simulator)
                p1_window = ParticipantControlWindow(simulator, "Управление участником 1")
                p2_window = ParticipantControlWindow(simulator, "Управление участником 2")
                
                # Запускаем главное окно
                main_window.mainloop()
            else:
                tk.messagebox.showerror("Ошибка", "Количество слотов должно быть от 1 до 10")
        except ValueError:
            tk.messagebox.showerror("Ошибка", "Введите корректное число")
    
    tk.Button(slots_window, text="Начать", command=start_simulation, font=("Arial", 12)).pack(pady=10)
    
    slots_window.mainloop()

if __name__ == "__main__":
    main() 