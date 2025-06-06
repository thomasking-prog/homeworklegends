# views/evaluation_create.py

import customtkinter as ctk
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.subject import Subject
from models.evaluation_note import EvaluationNote
from models.user import User
import utils.averages as avgs

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class EvaluationCreateWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Add Evaluation")
        self.geometry("400x450")
        self.current_user = current_user
        self.session = Session()

        self.label_label = ctk.CTkLabel(self, text="Label:")
        self.label_label.pack(pady=5)
        self.entry_label = ctk.CTkEntry(self)
        self.entry_label.pack(pady=5)

        self.label_score = ctk.CTkLabel(self, text="Score (0-20):")
        self.label_score.pack(pady=5)
        self.entry_score = ctk.CTkEntry(self)
        self.entry_score.pack(pady=5)

        self.label_date = ctk.CTkLabel(self, text="Date (YYYY-MM-DD):")
        self.label_date.pack(pady=5)
        self.entry_date = ctk.CTkEntry(self)
        self.entry_date.pack(pady=5)

        self.label_coeff = ctk.CTkLabel(self, text="Coefficient (default 1):")
        self.label_coeff.pack(pady=5)
        self.entry_coeff = ctk.CTkEntry(self, placeholder_text="1")
        self.entry_coeff.pack(pady=5)

        self.label_subject = ctk.CTkLabel(self, text="Subject:")
        self.label_subject.pack(pady=5)
        self.subject_box = ctk.CTkComboBox(self, values=[])
        self.subject_box.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=5)

        self.btn_submit = ctk.CTkButton(self, text="Add Evaluation", command=self.submit)
        self.btn_submit.pack(pady=15)

        self.load_subjects()

    def load_subjects(self):
        user = self.session.query(User).get(self.current_user.id)
        self.subjects = user.subjects
        self.subject_box.configure(values=[s.name for s in self.subjects])

    def submit(self):
        try:
            label = self.entry_label.get().strip()
            score = float(self.entry_score.get())
            date = datetime.strptime(self.entry_date.get(), "%Y-%m-%d").date()
            coeff = float(self.entry_coeff.get() or 1)
            subject_name = self.subject_box.get()

            if not label or not subject_name:
                raise ValueError("Missing data")

            subject = next((s for s in self.subjects if s.name == subject_name), None)
            if not subject:
                raise ValueError("Invalid subject")

            note = EvaluationNote(
                label=label,
                score=score,
                date=date,
                coefficient=coeff,
                user_id=self.current_user.id,
                subject_id=subject.id
            )
            self.session.add(note)
            user = self.session.merge(self.current_user)  # rattache à session
            avgs.update_rank_points(self.session, user, score)
            avgs.update_user_global_average(self.session, user)
            self.session.commit()

            self.status_label.configure(text="Evaluation added!", text_color="green")
            self.entry_label.delete(0, "end")
            self.entry_score.delete(0, "end")
            self.entry_date.delete(0, "end")
            self.entry_coeff.delete(0, "end")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")