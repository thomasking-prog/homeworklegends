# views/classroom_create.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.classroom import Classroom
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class ClassroomCreateWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create Classroom")
        self.geometry("400x300")

        self.label_name = ctk.CTkLabel(self, text="Classroom Name:")
        self.label_name.pack(pady=10)
        self.entry_name = ctk.CTkEntry(self)
        self.entry_name.pack(pady=10)

        self.label_desc = ctk.CTkLabel(self, text="Description:")
        self.label_desc.pack(pady=10)
        self.entry_desc = ctk.CTkEntry(self)
        self.entry_desc.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=10)

        self.btn_create = ctk.CTkButton(self, text="Create", command=self.create_classroom)
        self.btn_create.pack(pady=20)

    def create_classroom(self):
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()

        if not name:
            self.status_label.configure(text="Name is required", text_color="red")
            return

        session = Session()
        # Check if classroom exists
        if session.query(Classroom).filter_by(name=name).first():
            self.status_label.configure(text="Classroom already exists", text_color="red")
            session.close()
            return

        classroom = Classroom(name=name, description=desc)
        session.add(classroom)
        session.commit()
        session.close()

        self.status_label.configure(text="Classroom created!", text_color="green")
        self.entry_name.delete(0, "end")
        self.entry_desc.delete(0, "end")