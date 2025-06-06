# views/register.py

import customtkinter as ctk
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.user import User, RoleEnum
from views.dashboard import Dashboard

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class RegisterWindow(ctk.CTk):
    def __init__(self, parent_login):
        super().__init__()
        self.title("Register")
        self.geometry("400x400")
        self.parent_login = parent_login

        # First Name
        self.label_first = ctk.CTkLabel(self, text="First Name:")
        self.label_first.pack(pady=5)
        self.entry_first = ctk.CTkEntry(self)
        self.entry_first.pack(pady=5)

        # Last Name
        self.label_last = ctk.CTkLabel(self, text="Last Name:")
        self.label_last.pack(pady=5)
        self.entry_last = ctk.CTkEntry(self)
        self.entry_last.pack(pady=5)

        # Username
        self.label_username = ctk.CTkLabel(self, text="Username:")
        self.label_username.pack(pady=5)
        self.entry_username = ctk.CTkEntry(self)
        self.entry_username.pack(pady=5)

        # Password
        self.label_password = ctk.CTkLabel(self, text="Password:")
        self.label_password.pack(pady=5)
        self.entry_password = ctk.CTkEntry(self, show="*")
        self.entry_password.pack(pady=5)

        # Register Button
        self.button_register = ctk.CTkButton(self, text="Register", command=self.register)
        self.button_register.pack(pady=20)

        # Status
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

    def register(self):
        session = Session()

        first_name = self.entry_first.get().strip()
        last_name = self.entry_last.get().strip()
        username = self.entry_username.get().strip()
        password = self.entry_password.get()

        if not all([first_name, last_name, username, password]):
            self.status_label.configure(text="All fields are required", text_color="red")
            return

        # Check if user already exists
        if session.query(User).filter_by(username=username).first():
            self.status_label.configure(text="Username already exists", text_color="red")
            return

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=hashed_pw,
            role=RoleEnum.STUDENT
        )

        session.add(user)
        session.commit()

        # Auto-login : ouvrir le dashboard
        Dashboard(user, self.parent_login)
        self.parent_login.withdraw()
        self.destroy()