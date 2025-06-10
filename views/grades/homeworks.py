import customtkinter as ctk
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.homework import Homework, PriorityEnum
from models.subject import Subject
from models.user import User
from utils.scoring import apply_score_update

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

PRIORITY_COLOR = {
    "HIGH": "red",
    "MEDIUM": "orange",
    "LOW": "green"
}

class HomeworkView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.session = Session()

        # Frame scrollable globale
        self.main_scroll = ctk.CTkScrollableFrame(self)
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)



        # --- to do List devoirs à venir ---
        self.todo_frame = ctk.CTkFrame(self.main_scroll)
        self.todo_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.subjects = self.session.query(Subject).join(Subject.followers).filter(
            User.id == self.current_user.id).all()
        subject_names = [s.name for s in self.subjects]

        # --- Filtres matières ---
        subject_names = ["Toutes les matières"] + [s.name for s in self.subjects]
        self.subject_filter = ctk.CTkOptionMenu(self.todo_frame, values=subject_names,
                                                command=lambda _: self.load_homework_todo())
        self.subject_filter.set("Toutes les matières")
        self.subject_filter.pack(pady=5)

        ctk.CTkLabel(self.todo_frame, text="Upcoming Homework ToDo List", font=("Arial", 16)).pack(pady=10)
        self.todo_list_frame = ctk.CTkScrollableFrame(self.todo_frame)
        self.todo_list_frame.pack(fill="both", expand=True)

        # --- Liste devoirs à noter ---
        self.grade_frame = ctk.CTkFrame(self.main_scroll)
        self.grade_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.grade_frame, text="Homework to Grade", font=("Arial", 16)).pack(pady=10)
        self.grade_list_frame = ctk.CTkScrollableFrame(self.grade_frame)
        self.grade_list_frame.pack(fill="both", expand=True)

        # --- Création devoir ---

        # === Frame formulaire création ===
        self.create_frame = ctk.CTkFrame(self.main_scroll)
        self.create_frame.pack(padx=10, pady=10)
        self.create_frame.configure(width=400, height=350)
        self.create_frame.pack_propagate(False)

        ctk.CTkLabel(self.create_frame, text="Create Homework", font=("Arial", 16)).grid(row=0, column=0, columnspan=2,
                                                                                         pady=10)

        ctk.CTkLabel(self.create_frame, text="Title:").grid(row=1, column=0, sticky="w")
        self.entry_title = ctk.CTkEntry(self.create_frame)
        self.entry_title.grid(row=1, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(self.create_frame, text="Description:").grid(row=2, column=0, sticky="nw")
        self.entry_description = ctk.CTkTextbox(self.create_frame, height=60)
        self.entry_description.grid(row=2, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(self.create_frame, text="Due Date (YYYY-MM-DD):").grid(row=3, column=0, sticky="w")
        self.entry_due = ctk.CTkEntry(self.create_frame)
        self.entry_due.grid(row=3, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(self.create_frame, text="Priority:").grid(row=4, column=0, sticky="w")
        self.priority_box = ctk.CTkOptionMenu(self.create_frame, values=["LOW", "MEDIUM", "HIGH"])
        self.priority_box.set("MEDIUM")
        self.priority_box.grid(row=4, column=1, sticky="ew", pady=5)



        ctk.CTkLabel(self.create_frame, text="Subject:").grid(row=5, column=0, sticky="w")
        self.subject_box = ctk.CTkComboBox(self.create_frame, values=subject_names)
        self.subject_box.grid(row=5, column=1, sticky="ew", pady=5)

        self.btn_submit = ctk.CTkButton(self.create_frame, text="Create Homework", command=self.create_homework)
        self.btn_submit.grid(row=6, column=0, columnspan=2, pady=10)

        self.status_label = ctk.CTkLabel(self.create_frame, text="")
        self.status_label.grid(row=7, column=0, columnspan=2)

        self.create_frame.columnconfigure(1, weight=1)

        # Affiche les listes
        self.load_homework_todo()
        self.load_homework_to_grade()

    def create_homework(self):
        try:
            title = self.entry_title.get().strip()
            description = self.entry_description.get("0.0", "end").strip()
            due_date = datetime.strptime(self.entry_due.get(), "%Y-%m-%d").date()
            priority = PriorityEnum[self.priority_box.get()]

            subject_name = self.subject_box.get()
            subject = next((s for s in self.subjects if s.name == subject_name), None)

            if not title or not subject:
                raise ValueError("Missing title or subject")

            homework = Homework(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                user_id=self.current_user.id,
                subject_id=subject.id
            )
            self.session.add(homework)
            self.session.commit()

            self.status_label.configure(text="Homework created!", text_color="green")
            self.entry_title.delete(0, "end")
            self.entry_description.delete("0.0", "end")
            self.entry_due.delete(0, "end")

            self.load_homework_todo()  # Rafraîchit la to do list
            self.load_homework_to_grade()
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")

    def load_homework_todo(self):
        for widget in self.todo_list_frame.winfo_children():
            widget.destroy()

        selected_subject = self.subject_filter.get()
        subject_id = None
        if selected_subject != "Toutes les matières":
            subject = next((s for s in self.subjects if s.name == selected_subject), None)
            if subject:
                subject_id = subject.id

        query = (
            self.session.query(Homework)
            .filter(Homework.user_id == self.current_user.id)
            .filter(Homework.due_date >= date.today())
            .filter(Homework.grade == None)
        )

        if subject_id:
            query = query.filter(Homework.subject_id == subject_id)

        homework_list = query.order_by(Homework.due_date.asc(), Homework.priority.desc()).all()

        if not homework_list:
            ctk.CTkLabel(self.todo_list_frame, text="No upcoming homework.").pack(pady=10)
            return

        for hw in homework_list:
            frame = ctk.CTkFrame(self.todo_list_frame, border_width=1, border_color="gray")
            frame.pack(fill="x", pady=5, padx=5)

            priority_color = PRIORITY_COLOR[hw.priority.name]
            days_remaining = (hw.due_date - date.today()).days
            info = f"{hw.title} - {hw.subject.name} | Due in {days_remaining} day{'s' if days_remaining != 1 else ''}"
            label = ctk.CTkLabel(frame, text=info, text_color=priority_color, font=("Arial", 13))
            label.pack(side="left", anchor="w", padx=10, pady=5)

            btn_edit = ctk.CTkButton(frame, text="Edit", width=60, command=lambda hw=hw: self.open_edit_homework(hw))
            btn_edit.pack(side="right", padx=10)

            btn_delete = ctk.CTkButton(frame, text="Delete", width=60, fg_color="red",
                                       command=lambda hw=hw: self.delete_homework(hw))
            btn_delete.pack(side="right", padx=10)

    def load_homework_to_grade(self):
        for widget in self.grade_list_frame.winfo_children():
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
            ctk.CTkLabel(self.grade_list_frame, text="No homework to grade.").pack(pady=10)
            return

        for hw in homework_list:
            row = ctk.CTkFrame(self.grade_list_frame, border_width=1, border_color="gray")
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

            user = self.session.merge(self.current_user)  # rattache user
            # Utilise ta fonction centralisée pour update ranking + moyenne
            apply_score_update(self.session, user, value)

            self.session.commit()
            self.session.refresh(homework)
            self.session.refresh(user)

            self.load_homework_to_grade()  # rafraîchir la liste
            self.load_homework_todo()
        except Exception as e:
            entry_widget.delete(0, "end")
            entry_widget.configure(placeholder_text=str(e))

    def delete_homework(self, homework):
        try:
            self.session.delete(self.session.merge(homework))
            self.session.commit()
            self.load_homework_todo()  # Rafraîchit la liste
        except Exception as e:
            print(f"Error deleting homework: {e}")

    def open_edit_homework(self, homework):
        edit_win = ctk.CTkToplevel(self)
        edit_win.title("Edit Homework")
        edit_win.geometry("400x400")

        # Champs du formulaire pré-remplis
        ctk.CTkLabel(edit_win, text="Title:").pack(pady=5)
        entry_title = ctk.CTkEntry(edit_win)
        entry_title.insert(0, homework.title)
        entry_title.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Description:").pack(pady=5)
        entry_desc = ctk.CTkTextbox(edit_win, height=80)
        entry_desc.insert("0.0", homework.description or "")
        entry_desc.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Due Date (YYYY-MM-DD):").pack(pady=5)
        entry_due = ctk.CTkEntry(edit_win)
        entry_due.insert(0, str(homework.due_date))
        entry_due.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Priority:").pack(pady=5)
        priority_box = ctk.CTkOptionMenu(edit_win, values=["LOW", "MEDIUM", "HIGH"])
        priority_box.set(homework.priority.name)
        priority_box.pack(pady=5)

        # Optionnel: Subject dropdown si tu veux modifier la matière
        # subjects = self.session.query(Subject).all()
        # subject_names = [s.name for s in subjects]
        # subject_dropdown = ctk.CTkOptionMenu(edit_win, values=subject_names)
        # subject_dropdown.set(homework.subject.name if homework.subject else subject_names[0])
        # subject_dropdown.pack(pady=5)

        def save_changes():
            try:
                homework.title = entry_title.get().strip()
                homework.description = entry_desc.get("0.0", "end").strip()
                homework.due_date = datetime.strptime(entry_due.get(), "%Y-%m-%d").date()
                homework.priority = PriorityEnum[priority_box.get()]

                # Si gestion matière modifiable :
                # subject_name = subject_dropdown.get()
                # subject = next((s for s in subjects if s.name == subject_name), None)
                # if subject:
                #     homework.subject_id = subject.id

                self.session.commit()
                edit_win.destroy()
                self.load_homework_todo()  # ou ta méthode de rafraîchissement
            except Exception as e:
                # Gestion erreur simple
                ctk.CTkLabel(edit_win, text=f"Error: {str(e)}", text_color="red").pack()

        ctk.CTkButton(edit_win, text="Save", command=save_changes).pack(pady=20)

