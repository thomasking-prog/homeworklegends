# views/homework_grade.py

import customtkinter as ctk
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.homework import Homework
import utils.averages as avgs

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class HomeworkGradeWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Grade Past Homework")
        self.geometry("700x500")
        self.current_user = current_user
        self.session = Session()

        self.label = ctk.CTkLabel(self, text="Homework to Grade", font=("Arial", 16))
        self.label.pack(pady=10)

        self.grade_frame = ctk.CTkScrollableFrame(self)
        self.grade_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_homework()

    def load_homework(self):
        for widget in self.grade_frame.winfo_children():
            widget.destroy()

        homework_list = (
            self.session.query(Homework)
            .filter(Homework.user_id == self.current_user.id)
            .filter(Homework.due_date <= date.today())
            .filter(Homework.grade == None)
            .order_by(Homework.due_date.desc())
            .all()
        )

        if not homework_list:
            ctk.CTkLabel(self.grade_frame, text="No homework to grade.").pack(pady=10)
            return

        for hw in homework_list:
            row = ctk.CTkFrame(self.grade_frame, border_width=1, border_color="gray")
            row.pack(fill="x", padx=5, pady=5)

            title = f"{hw.title} ({hw.subject.name}) - Due {hw.due_date}"
            ctk.CTkLabel(row, text=title).pack(side="left", padx=10)

            entry = ctk.CTkEntry(row, width=50, placeholder_text="Note /20")
            entry.pack(side="left", padx=10)

            submit_btn = ctk.CTkButton(row, text="Save", command=lambda h=hw, e=entry: self.save_grade(h, e))
            submit_btn.pack(side="right", padx=10)

    def save_grade(self, homework, entry_widget):
        try:
            value = float(entry_widget.get())
            if not (0 <= value <= 20):
                raise ValueError("Note must be between 0 and 20")

            homework.grade = value
            self.session.add(homework)
            user = self.session.merge(self.current_user)  # rattache à session
            avgs.update_rank_points(self.session, user, value)
            avgs.update_user_global_average(self.session, user)
            self.session.commit()
            self.session.refresh(homework)
            self.session.refresh(user)

            self.load_homework()
        except Exception as e:
            entry_widget.delete(0, "end")
            entry_widget.configure(placeholder_text=str(e))