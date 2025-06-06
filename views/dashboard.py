# views/dashboard.py

import customtkinter as ctk

from views.classroom_create import ClassroomCreateWindow
from views.classroom_join import ClassroomJoinWindow
from views.classroom_requests import ClassroomRequestWindow
from views.subject_manage import SubjectManageWindow
from views.subject_follow import SubjectFollowWindow
from views.evaluation_create import EvaluationCreateWindow
from views.evaluation_list import EvaluationListWindow
from views.homework_create import HomeworkCreateWindow
from views.homework_todolist import HomeworkTodoListWindow
from views.homework_grade import HomeworkGradeWindow
from views.notes_chart import NotesChartWindow
from views.rank_manager import RankManagerWindow


class Dashboard(ctk.CTkToplevel):
    def __init__(self, user, parent_window):
        super().__init__()
        self.title("Dashboard")
        self.geometry("500x300")
        self.current_user = user  # ✅ On stocke l'utilisateur ici
        self.parent_window = parent_window  # La fenêtre de connexion à réafficher

        welcome = f"Welcome {user.first_name} {user.last_name} ({user.username})"
        self.label_welcome = ctk.CTkLabel(self, text=welcome, font=("Helvetica", 16))
        self.label_welcome.pack(pady=20)

        self.label_role = ctk.CTkLabel(self, text=f"Your role: {user.role.value}")
        self.label_role.pack(pady=5)

        rank = self.current_user.rank
        rank_name = rank.name if rank else "Unranked"
        rank_color = rank.color if rank and rank.color else "#4287f5"

        self.rank_label = ctk.CTkLabel(
            self,
            text=f"🏆 Rank: {rank_name}",
            text_color=rank_color,
            font=("Arial", 14, "bold")
        )
        self.rank_label.pack(pady=10)

        classroom = self.current_user.classroom
        if classroom:
            class_info = (
                f"🏫 Class: {classroom.name} | ELO: {classroom.rank_points_avg:.2f}"
                if classroom.rank_points_avg else
                f"🏫 Class: {classroom.name} | ELO: N/A"
            )
            self.class_label = ctk.CTkLabel(
                self,
                text=class_info,
                font=("Arial", 13)
            )
            self.class_label.pack(pady=5)

        self.label_info = ctk.CTkLabel(self, text="(Navigation buttons will go here...)")
        self.label_info.pack(pady=10)


        if self.current_user.role.value == "admin":
            # Create Classroom button
            self.btn_create_class = ctk.CTkButton(self, text="Create Classroom", command=self.open_create_class)
            self.btn_create_class.pack(pady=10)

            # Create Subject button
            self.btn_subjects = ctk.CTkButton(self, text="Manage Subjects", command=self.open_subjects)
            self.btn_subjects.pack(pady=5)


        # Join Subject button
        self.btn_follow_subjects = ctk.CTkButton(self, text="My Subjects", command=self.open_subject_follow)
        self.btn_follow_subjects.pack(pady=5)

        # Add Evaluation button
        self.btn_eval = ctk.CTkButton(self, text="Add Evaluation", command=self.open_evaluation)
        self.btn_eval.pack(pady=5)

        # View Evaluations button
        self.btn_list_eval = ctk.CTkButton(self, text="View Evaluations", command=self.open_eval_list)
        self.btn_list_eval.pack(pady=5)

        # Join Classroom button
        self.btn_join_class = ctk.CTkButton(self, text="Join Classroom", command=self.open_join_class)
        self.btn_join_class.pack(pady=10)

        # Create Homework button
        self.btn_homework = ctk.CTkButton(self, text="Create Homework", command=self.open_homework)
        self.btn_homework.pack(pady=5)

        # List Homework button
        self.btn_todolist = ctk.CTkButton(self, text="ToDo List", command=self.open_todolist)
        self.btn_todolist.pack(pady=5)

        # Grade Homework button
        self.btn_grade_hw = ctk.CTkButton(self, text="Grade Homework", command=self.open_grade_hw)
        self.btn_grade_hw.pack(pady=5)

        # Notes Chart button
        self.btn_chart = ctk.CTkButton(self, text="View Notes Chart", command=self.open_notes_chart)
        self.btn_chart.pack(pady=5)

        # Rank Management
        self.btn_rank_mgmt = ctk.CTkButton(self, text="Manage Ranks", command=self.open_rank_mgmt)
        self.btn_rank_mgmt.pack(pady=5)

        if self.current_user.role.value in ["admin", "delegate"]:
            self.btn_requests = ctk.CTkButton(self, text="Manage Join Requests", command=self.open_requests)
            self.btn_requests.pack(pady=10)

        # Logout button
        self.logout_button = ctk.CTkButton(self, text="Logout", command=self.logout)
        self.logout_button.pack(pady=20)

    def open_rank_mgmt(self):
        RankManagerWindow(self)

    def open_notes_chart(self):
        NotesChartWindow(self, self.current_user)

    def open_grade_hw(self):
        HomeworkGradeWindow(self, self.current_user)

    def open_todolist(self):
        HomeworkTodoListWindow(self, self.current_user)

    def open_homework(self):
        HomeworkCreateWindow(self, self.current_user)

    def open_eval_list(self):
        EvaluationListWindow(self, self.current_user)

    def open_evaluation(self):
        EvaluationCreateWindow(self, self.current_user)

    def open_subject_follow(self):
        SubjectFollowWindow(self, self.current_user)

    def open_subjects(self):
        SubjectManageWindow(self, self.current_user)

    def open_requests(self):
        ClassroomRequestWindow(self, self.current_user)

    def open_create_class(self):
        ClassroomCreateWindow(self)

    def open_join_class(self):
        ClassroomJoinWindow(self, self.current_user)

    def logout(self):
        self.destroy()  # Ferme le dashboard
        self.parent_window.deiconify()  # Réaffiche la fenêtre de login