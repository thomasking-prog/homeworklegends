# views/subject_manage.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.subject import Subject
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class SubjectManageWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Manage Subjects")
        self.geometry("500x400")
        self.current_user = current_user
        self.session = Session()

        self.label = ctk.CTkLabel(self, text="Add New Subject")
        self.label.pack(pady=10)

        self.entry_subject = ctk.CTkEntry(self, placeholder_text="Subject name")
        self.entry_subject.pack(pady=5)

        self.btn_add = ctk.CTkButton(self, text="Add Subject", command=self.add_subject)
        self.btn_add.pack(pady=5)

        self.label_list = ctk.CTkLabel(self, text="Existing Subjects:")
        self.label_list.pack(pady=10)

        self.subjects_frame = ctk.CTkScrollableFrame(self)
        self.subjects_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_subjects()

    def add_subject(self):
        name = self.entry_subject.get().strip()
        if not name:
            return

        existing = self.session.query(Subject).filter_by(name=name).first()
        if existing:
            self.entry_subject.delete(0, "end")
            self.entry_subject.configure(placeholder_text="Subject already exists")
            return

        subject = Subject(name=name)
        self.session.add(subject)
        self.session.commit()
        self.entry_subject.delete(0, "end")
        self.refresh_subjects()

    def delete_subject(self, subject_id):
        subject = self.session.query(Subject).get(subject_id)
        if subject:
            self.session.delete(subject)
            self.session.commit()
            self.refresh_subjects()

    def refresh_subjects(self):
        for widget in self.subjects_frame.winfo_children():
            widget.destroy()

        subjects = self.session.query(Subject).all()
        for subject in subjects:
            row = ctk.CTkFrame(self.subjects_frame)
            row.pack(pady=5, fill="x", padx=5)

            label = ctk.CTkLabel(row, text=subject.name)
            label.pack(side="left", padx=5)

            delete_btn = ctk.CTkButton(
                row, text="Delete", fg_color="red",
                command=lambda sid=subject.id: self.delete_subject(sid)
            )
            delete_btn.pack(side="right", padx=5)