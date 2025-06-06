# views/subject_follow.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.subject import Subject
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class SubjectFollowWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Follow Subjects")
        self.geometry("500x400")
        self.current_user = current_user
        self.session = Session()

        self.label = ctk.CTkLabel(self, text="Manage Your Subjects")
        self.label.pack(pady=10)

        self.subjects_frame = ctk.CTkScrollableFrame(self)
        self.subjects_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_subjects()

    def refresh_subjects(self):
        for widget in self.subjects_frame.winfo_children():
            widget.destroy()

        db_user = self.session.query(User).get(self.current_user.id)
        followed_ids = {s.id for s in db_user.subjects}
        subjects = self.session.query(Subject).all()

        for subject in subjects:
            row = ctk.CTkFrame(self.subjects_frame)
            row.pack(pady=5, fill="x", padx=5)

            label = ctk.CTkLabel(row, text=subject.name)
            label.pack(side="left", padx=5)

            if subject.id in followed_ids:
                btn = ctk.CTkButton(row, text="Unfollow", fg_color="red", command=lambda s=subject: self.unfollow(s))
            else:
                btn = ctk.CTkButton(row, text="Follow", fg_color="green", command=lambda s=subject: self.follow(s))
            btn.pack(side="right", padx=5)

    def follow(self, subject):
        user = self.session.query(User).get(self.current_user.id)
        user.subjects.append(subject)
        self.session.commit()
        self.refresh_subjects()

    def unfollow(self, subject):
        user = self.session.query(User).get(self.current_user.id)
        user.subjects.remove(subject)
        self.session.commit()
        self.refresh_subjects()