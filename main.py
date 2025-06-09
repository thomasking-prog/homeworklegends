# main.py

import customtkinter as ctk
from views.login import LoginWindow

if __name__ == "__main__":
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    app = LoginWindow()
    app.mainloop()