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
from models.subject import Subject
from datetime import datetime

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class StatisticsView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.session = Session()

        ctk.CTkLabel(self, text="Statistiques", font=("Arial", 24)).pack(pady=15)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Mes Notes")
        self.tabview.add("Classement Students")
        self.tabview.add("Classements Classes")

        self.notes_tab = self.tabview.tab("Mes Notes")
        self.rank_tab = self.tabview.tab("Classement Students")
        self.classroom_rank_tab = self.tabview.tab("Classements Classes")

        self.init_notes_tab()
        self.init_ranking_tab()
        self.init_classroom_ranking_tab()

    def init_notes_tab(self):
        self.view_mode = ctk.StringVar(value="Daily Average")
        # Liste des matières suivies
        self.subjects = self.session.query(Subject).join(Subject.followers).filter(
            User.id == self.current_user.id).all()
        subject_names = ["Toutes les matières"] + [s.name for s in self.subjects]

        self.subject_filter = ctk.CTkOptionMenu(
            self.notes_tab,
            values=subject_names,
            command=lambda _: self.draw_chart()
        )
        self.subject_filter.set("Toutes les matières")
        self.subject_filter.pack(pady=5)

        self.note_type = ctk.StringVar(value="Toutes")
        self.type_filter = ctk.CTkOptionMenu(
            self.notes_tab,
            values=["Toutes", "Évaluations", "Devoirs"],
            variable=self.note_type,
            command=lambda _: self.draw_chart()
        )
        self.type_filter.pack(pady=5)

        self.mode_selector = ctk.CTkOptionMenu(
            self.notes_tab, values=["All Notes", "Daily Average", "Monthly Average"],
            variable=self.view_mode, command=lambda _: self.draw_chart()
        )
        self.mode_selector.pack(pady=10)

        self.chart_container = ctk.CTkFrame(self.notes_tab)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=5)
        self.canvas = None
        self.draw_chart()

    def draw_chart(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        for widget in self.chart_container.winfo_children():
            widget.destroy()

        evaluations = self.session.query(EvaluationNote).filter_by(user_id=self.current_user.id).order_by(EvaluationNote.date.asc()).all()
        homeworks = self.session.query(Homework).filter(Homework.user_id == self.current_user.id, Homework.grade != None).order_by(Homework.due_date.asc()).all()

        selected_subject = self.subject_filter.get()
        if selected_subject != "Toutes les matières":
            selected = next((s for s in self.subjects if s.name == selected_subject), None)
            if selected:
                evaluations = [e for e in evaluations if e.subject_id == selected.id]
                homeworks = [h for h in homeworks if h.subject_id == selected.id]

        selected_type = self.note_type.get()
        if selected_type == "Évaluations":
            homeworks = []
        elif selected_type == "Devoirs":
            evaluations = []

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
            for d in sorted(grouped):
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
            for d in sorted(grouped):
                avg = sum(grouped[d]) / len(grouped[d])
                points.append((d, avg))

        if not points:
            ctk.CTkLabel(self.chart_container, text="No data to display.").pack(pady=20)
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

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        plt.close(fig)  # 🔁 Ajoute ceci pour éviter de garder des états matplotlib

    def init_ranking_tab(self):
        users = self.session.query(User).filter(User.role == "STUDENT", User.classroom_id != None).order_by(User.rank_points.desc()).all()

        table = ctk.CTkScrollableFrame(self.rank_tab)
        table.pack(fill="both", expand=True, padx=10, pady=10)

        headers = ["Nom d'utilisateur", "Rang", "Points", "Classe"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(table, text=text, font=("Arial", 14, "bold")).grid(row=0, column=col, padx=5, pady=5)

        for row, user in enumerate(users, start=1):
            ctk.CTkLabel(table, text=user.username).grid(row=row, column=0, padx=5, pady=5)
            ctk.CTkLabel(table, text=user.rank.name if user.rank else "Unranked").grid(row=row, column=1, padx=5, pady=5)
            ctk.CTkLabel(table, text=int(user.rank_points)).grid(row=row, column=2, padx=5, pady=5)
            ctk.CTkLabel(table, text=user.classroom.name if user.classroom else "-").grid(row=row, column=3, padx=5, pady=5)

    def init_classroom_ranking_tab(self):
        from models.classroom import Classroom  # ✅ au cas où ce n’est pas importé en haut

        classrooms = (
            self.session.query(Classroom)
            .filter(Classroom.rank_points_avg != None)
            .order_by(Classroom.rank_points_avg.desc())
            .all()
        )

        table = ctk.CTkScrollableFrame(self.classroom_rank_tab)
        table.pack(fill="both", expand=True, padx=10, pady=10)

        headers = ["Nom de la classe", "Moyenne ELO", "Rang", "Nombre d'élèves"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(table, text=text, font=("Arial", 14, "bold")).grid(row=0, column=col, padx=5, pady=5)

        for row, classroom in enumerate(classrooms, start=1):
            ctk.CTkLabel(table, text=classroom.name).grid(row=row, column=0, padx=5, pady=5)
            ctk.CTkLabel(table, text=f"{int(classroom.rank_points_avg)}").grid(row=row, column=1, padx=5, pady=5)
            ctk.CTkLabel(table, text=classroom.rank.name if classroom.rank else "Unranked").grid(row=row, column=2, padx=5, pady=5)
            ctk.CTkLabel(table, text=str(len(classroom.users))).grid(row=row, column=3, padx=5, pady=5)

