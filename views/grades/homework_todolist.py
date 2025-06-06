# views/homework_todolist.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.homework import Homework, PriorityEnum
from models.subject import Subject
from models.user import User
from datetime import date

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

PRIORITY_COLOR = {
    "HIGH": "red",
    "MEDIUM": "orange",
    "LOW": "green"
}

class HomeworkTodoListWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("My Homework ToDo List")
        self.geometry("700x500")
        self.current_user = current_user
        self.session = Session()

        self.label = ctk.CTkLabel(self, text="Upcoming Homework", font=("Arial", 16))
        self.label.pack(pady=10)

        self.todo_frame = ctk.CTkScrollableFrame(self)
        self.todo_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_homework()

    def load_homework(self):
        for widget in self.todo_frame.winfo_children():
            widget.destroy()

        homework_list = (
            self.session.query(Homework)
            .filter(Homework.user_id == self.current_user.id)
            .filter(Homework.due_date >= date.today())
            .order_by(Homework.due_date.asc(), Homework.priority.desc())
            .all()
        )

        if not homework_list:
            ctk.CTkLabel(self.todo_frame, text="No upcoming homework.").pack(pady=10)
            return

        for hw in homework_list:
            frame = ctk.CTkFrame(self.todo_frame, border_width=1, border_color="gray")
            frame.pack(fill="x", pady=5, padx=5)

            priority_color = PRIORITY_COLOR[hw.priority.name]

            info = f"{hw.title} - {hw.subject.name} | Due: {hw.due_date} | Priority: {hw.priority.name.capitalize()}"
            label = ctk.CTkLabel(frame, text=info, text_color=priority_color, font=("Arial", 13))
            label.pack(anchor="w", padx=10, pady=5)