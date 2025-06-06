# views/homework_create.py

import customtkinter as ctk
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.homework import Homework, PriorityEnum
from models.subject import Subject
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class HomeworkCreateWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Create Homework")
        self.geometry("500x500")
        self.current_user = current_user
        self.session = Session()

        ctk.CTkLabel(self, text="Title:").pack(pady=5)
        self.entry_title = ctk.CTkEntry(self)
        self.entry_title.pack(pady=5)

        ctk.CTkLabel(self, text="Description:").pack(pady=5)
        self.entry_description = ctk.CTkTextbox(self, height=80)
        self.entry_description.pack(pady=5)

        ctk.CTkLabel(self, text="Due Date (YYYY-MM-DD):").pack(pady=5)
        self.entry_due = ctk.CTkEntry(self)
        self.entry_due.pack(pady=5)

        ctk.CTkLabel(self, text="Priority:").pack(pady=5)
        self.priority_box = ctk.CTkOptionMenu(self, values=["LOW", "MEDIUM", "HIGH"])
        self.priority_box.set("MEDIUM")
        self.priority_box.pack(pady=5)

        ctk.CTkLabel(self, text="Subject:").pack(pady=5)
        self.subject_box = ctk.CTkComboBox(self, values=[])
        self.subject_box.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=5)

        self.btn_submit = ctk.CTkButton(self, text="Create Homework", command=self.create_homework)
        self.btn_submit.pack(pady=20)

        self.load_subjects()

    def load_subjects(self):
        user = self.session.query(User).get(self.current_user.id)
        self.subjects = user.subjects
        self.subject_box.configure(values=[s.name for s in self.subjects])

    def create_homework(self):
        try:
            title = self.entry_title.get().strip()
            description = self.entry_description.get("0.0", "end").strip()
            due_date = datetime.strptime(self.entry_due.get(), "%Y-%m-%d").date()
            priority_str = self.priority_box.get()
            priority = PriorityEnum[priority_str]

            subject_name = self.subject_box.get()
            subject = next((s for s in self.subjects if s.name == subject_name), None)

            if not title or not subject:
                raise ValueError("Missing title or subject")

            homework = Homework(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                user_id=self.current_user.id,
                subject_id=subject.id
            )

            self.session.add(homework)
            self.session.commit()
            self.status_label.configure(text="Homework created!", text_color="green")
            self.entry_title.delete(0, "end")
            self.entry_description.delete("0.0", "end")
            self.entry_due.delete(0, "end")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")