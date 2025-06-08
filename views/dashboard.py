# views/dashboard.py

import customtkinter as ctk
from views.admin.classroom_create import ClassroomCreateWindow
from views.classroom_join import ClassroomJoinWindow
from views.delegate.classroom_requests import ClassroomRequestWindow
from views.subject_manage import SubjectManageWindow
from views.subject_follow import SubjectFollowWindow
from views.grades.notes_chart import NotesChartWindow
from views.admin.rank_manager import RankManagerWindow


class Dashboard(ctk.CTkToplevel):
    def __init__(self, user, parent_window):
        super().__init__()


        if self.current_user.role.value == "admin":
            # Create Classroom button
            self.btn_create_class = ctk.CTkButton(self, text="Create Classroom", command=self.open_create_class)
            self.btn_create_class.pack(pady=10)

            # Create Subject button
            self.btn_subjects = ctk.CTkButton(self, text="Manage Subjects", command=self.open_subjects)
            self.btn_subjects.pack(pady=5)

        # Join Classroom button
        self.btn_join_class = ctk.CTkButton(self, text="Join Classroom", command=self.open_join_class)
        self.btn_join_class.pack(pady=10)

        # Notes Chart button
        self.btn_chart = ctk.CTkButton(self, text="View Notes Chart", command=self.open_notes_chart)
        self.btn_chart.pack(pady=5)

        # Rank Management
        self.btn_rank_mgmt = ctk.CTkButton(self, text="Manage Ranks", command=self.open_rank_mgmt)
        self.btn_rank_mgmt.pack(pady=5)

        if self.current_user.role.value in ["admin", "delegate"]:
            self.btn_requests = ctk.CTkButton(self, text="Manage Join Requests", command=self.open_requests)
            self.btn_requests.pack(pady=10)

    def open_rank_mgmt(self):
        RankManagerWindow(self)

    def open_notes_chart(self):
        NotesChartWindow(self, self.current_user)

    def open_subjects(self):
        SubjectManageWindow(self, self.current_user)

    def open_requests(self):
        ClassroomRequestWindow(self, self.current_user)

    def open_create_class(self):
        ClassroomCreateWindow(self)

    def open_join_class(self):
        ClassroomJoinWindow(self, self.current_user)