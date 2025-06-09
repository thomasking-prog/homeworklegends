# views/login.py

import customtkinter as ctk
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.user import User
from views.new_dashboard import MainApp
from views.register import RegisterWindow

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("400x300")

        self.label_username = ctk.CTkLabel(self, text="Username:")
        self.label_username.pack(pady=5)
        self.entry_username = ctk.CTkEntry(self)
        self.entry_username.pack(pady=5)

        self.label_password = ctk.CTkLabel(self, text="Password:")
        self.label_password.pack(pady=5)
        self.entry_password = ctk.CTkEntry(self, show="*")
        self.entry_password.pack(pady=5)

        self.button_login = ctk.CTkButton(self, text="Login", command=self.login)
        self.button_login.pack(pady=20)

        # Register button
        self.button_register = ctk.CTkButton(self, text="Register", command=self.open_register)
        self.button_register.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

    def open_register(self):
        self.withdraw()
        register_window = RegisterWindow(self)

        def on_close():
            self.deiconify()
            register_window.destroy()

        register_window.protocol("WM_DELETE_WINDOW", on_close)
        register_window.mainloop()  # <-- Ajoute cette ligne

    def login(self):
        session = Session()

        username = self.entry_username.get().strip()
        password = self.entry_password.get()

        user = session.query(User).filter_by(username=username).first()
        if user is None:
            self.status_label.configure(text="User not found", text_color="red")
            return

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            self.status_label.configure(text="Incorrect password", text_color="red")
            return

        self.status_label.configure(text="Login successful!", text_color="green")
        print(f"Logged in as {user.username} with role {user.role.value}")

        # 👉 Crée et ouvre le dashboard principal
        dashboard = MainApp(user, self)

        # 👉 Ferme ou cache la fenêtre login
        self.withdraw()

        # ✅ Attendre que MainApp se ferme
        dashboard.mainloop()

        # 👉 Quand dashboard se ferme, réaffiche login
        self.deiconify()
