import customtkinter as ctk
from views import EvaluationView, HomeworkView, ProfileView, AdminView, StatisticsView, DelegateView

class MainApp(ctk.CTk):
    def __init__(self, current_user, parent_window):
        super().__init__()
        self.title("Homework Legends")
        self.geometry("1000x700")
        self.current_user = current_user
        self.parent_window = parent_window

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.navbar = ctk.CTkFrame(self, width=200)
        self.navbar.grid(row=0, column=0, sticky="ns")

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkButton(self.navbar, text="Évaluations", command=self.show_evaluations).pack(pady=10)
        ctk.CTkButton(self.navbar, text="Devoirs", command=self.show_homework).pack(pady=10)
        ctk.CTkButton(self.navbar, text="Statistiques", command=self.show_statistics).pack(pady=10)
        ctk.CTkButton(self.navbar, text="Mon profil", command=self.show_profile).pack(pady=10)

        if self.current_user.role.value == "delegate":
            ctk.CTkButton(self.navbar, text="Demandes de classe", fg_color="green", command=self.show_delegate).pack(pady=10)

        # Bouton admin visible seulement si admin
        if self.current_user.role.value == "admin":
            ctk.CTkButton(self.navbar, text="Admin", fg_color="red", command=self.show_admin).pack(pady=10)


        ctk.CTkButton(self.navbar, text="Se déconnecter", command=self.logout).pack(pady=10)

        self.current_view = None
        self.show_homework()

    def clear_main_frame(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = None

    def show_statistics(self):
        self.clear_main_frame()
        self.current_view = StatisticsView(self.main_frame, self.current_user)
        self.current_view.pack(fill="both", expand=True)

    def show_evaluations(self):
        self.clear_main_frame()
        self.current_view = EvaluationView(self.main_frame, self.current_user)
        self.current_view.pack(fill="both", expand=True)

    def show_homework(self):
        self.clear_main_frame()
        self.current_view = HomeworkView(self.main_frame, self.current_user)
        self.current_view.pack(fill="both", expand=True)

    def show_profile(self):
        self.clear_main_frame()
        self.current_view = ProfileView(self.main_frame, self.current_user)
        self.current_view.pack(fill="both", expand=True)

    def show_admin(self):
        self.clear_main_frame()
        self.current_view = AdminView(self.main_frame, self.current_user)
        self.current_view.pack(fill="both", expand=True)

    def show_delegate(self):
        self.clear_main_frame()
        self.current_view = DelegateView(self.main_frame, self.current_user)
        self.current_view.pack(fill="both", expand=True)

    def logout(self):
        self.destroy()
        self.parent_window.deiconify()
