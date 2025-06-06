# views/notes_chart.py

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.evaluation_note import EvaluationNote
from models.homework import Homework
from models.user import User
from collections import defaultdict
from datetime import datetime

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class NotesChartWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Notes Chart")
        self.geometry("800x600")
        self.current_user = current_user
        self.session = Session()

        self.view_mode = ctk.StringVar(value="Daily Average")

        self.mode_selector = ctk.CTkOptionMenu(
            self, values=["All Notes", "Daily Average", "Monthly Average"],
            variable=self.view_mode,
            command=lambda _: self.draw_chart()
        )
        self.mode_selector.pack(pady=10)

        self.canvas = None

        self.draw_chart()

    def draw_chart(self):
        # Nettoyer l'ancien graphique s'il existe
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        evaluations = (
            self.session.query(EvaluationNote)
            .filter_by(user_id=self.current_user.id)
            .order_by(EvaluationNote.date.asc())
            .all()
        )
        homeworks = (
            self.session.query(Homework)
            .filter(Homework.user_id == self.current_user.id, Homework.grade != None)
            .order_by(Homework.due_date.asc())
            .all()
        )

        mode = self.view_mode.get()
        points = []

        if mode == "All Notes":
            for ev in evaluations:
                points.append((ev.date, ev.score))
            for hw in homeworks:
                points.append((hw.due_date, hw.grade))

        elif mode == "Daily Average":
            grouped = defaultdict(list)
            for ev in evaluations:
                grouped[ev.date].append(ev.score)
            for hw in homeworks:
                grouped[hw.due_date].append(hw.grade)

            for d in sorted(grouped.keys()):
                avg = sum(grouped[d]) / len(grouped[d])
                points.append((d, avg))

        elif mode == "Monthly Average":
            grouped = defaultdict(list)
            for ev in evaluations:
                key = ev.date.replace(day=1)
                grouped[key].append(ev.score)
            for hw in homeworks:
                key = hw.due_date.replace(day=1)
                grouped[key].append(hw.grade)

            for month in sorted(grouped.keys()):
                avg = sum(grouped[month]) / len(grouped[month])
                points.append((month, avg))

        if not points:
            ctk.CTkLabel(self, text="No data to display.").pack(pady=20)
            return

        points.sort()
        dates, values = zip(*points)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, values, marker="o", linestyle="-", color="blue")
        ax.set_title(f"{mode} of Notes")
        ax.set_xlabel("Date")
        ax.set_ylabel("Score (/20)")
        ax.set_ylim(0, 20)
        ax.grid(True)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)