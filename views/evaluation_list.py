# views/evaluation_list.py (vue tabulaire améliorée)

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.evaluation_note import EvaluationNote
from models.user import User
from models.subject import Subject

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class EvaluationListWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Your Evaluations")
        self.geometry("800x600")
        self.current_user = current_user
        self.session = Session()

        self.filters_frame = ctk.CTkFrame(self)
        self.filters_frame.pack(pady=10, padx=10, fill="x")

        self.filter_label = ctk.CTkEntry(self.filters_frame, placeholder_text="Filter by label...")
        self.filter_label.pack(side="left", padx=5)

        self.subjects = self.session.query(Subject).join(Subject.followers).filter(User.id == self.current_user.id).all()
        subject_names = [s.name for s in self.subjects]
        self.subject_filter = ctk.CTkOptionMenu(self.filters_frame, values=["All"] + subject_names)
        self.subject_filter.set("All")
        self.subject_filter.pack(side="left", padx=5)

        self.apply_filter_btn = ctk.CTkButton(self.filters_frame, text="Apply Filters", command=self.render_table)
        self.apply_filter_btn.pack(side="left", padx=5)

        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.render_table()

    def render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = ["Date", "Label", "Subject", "Score (/20)", "Coefficient", "Actions"]
        for col, title in enumerate(headers):
            header = ctk.CTkLabel(self.table_frame, text=title, font=("Arial", 13, "bold"))
            header.grid(row=0, column=col, padx=1, pady=2, sticky="nsew")

        query = self.session.query(EvaluationNote).filter_by(user_id=self.current_user.id)

        # Filtrage par label
        label_filter = self.filter_label.get().strip().lower()
        if label_filter:
            query = query.filter(EvaluationNote.label.ilike(f"%{label_filter}%"))

        # Filtrage par matière
        selected_subject = self.subject_filter.get()
        if selected_subject != "All":
            subj = next((s for s in self.subjects if s.name == selected_subject), None)
            if subj:
                query = query.filter(EvaluationNote.subject_id == subj.id)

        evaluations = query.order_by(EvaluationNote.date.desc()).all()

        for row_idx, note in enumerate(evaluations, start=1):
            subject = note.subject.name if note.subject else "Unknown"
            row_data = [
                str(note.date),
                note.label,
                subject,
                f"{note.score:.1f}",
                f"{note.coefficient:.1f}"
            ]
            for col_idx, value in enumerate(row_data):
                frame = ctk.CTkFrame(self.table_frame, border_width=1, border_color="gray")
                frame.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")
                label = ctk.CTkLabel(frame, text=value)
                label.pack(padx=4, pady=2)

            action_frame = ctk.CTkFrame(self.table_frame, border_width=1, border_color="gray")
            action_frame.grid(row=row_idx, column=5, padx=1, pady=1, sticky="nsew")
            btn_edit = ctk.CTkButton(action_frame, text="Edit", width=60, command=lambda nid=note.id: self.edit_evaluation(nid))
            btn_edit.pack(side="left", padx=2, pady=2)
            btn_del = ctk.CTkButton(action_frame, text="Delete", fg_color="red", width=60, command=lambda nid=note.id: self.delete_evaluation(nid))
            btn_del.pack(side="right", padx=2, pady=2)

    def delete_evaluation(self, note_id):
        note = self.session.query(EvaluationNote).get(note_id)
        if note:
            self.session.delete(note)
            self.session.commit()
            self.render_table()

    def edit_evaluation(self, note_id):
        note = self.session.query(EvaluationNote).get(note_id)
        if note:
            self.open_edit_window(note)

    def open_edit_window(self, note):
        edit_win = ctk.CTkToplevel(self)
        edit_win.title("Edit Evaluation")
        edit_win.geometry("400x400")

        ctk.CTkLabel(edit_win, text="Label:").pack(pady=5)
        entry_label = ctk.CTkEntry(edit_win)
        entry_label.insert(0, note.label)
        entry_label.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Score (0-20):").pack(pady=5)
        entry_score = ctk.CTkEntry(edit_win)
        entry_score.insert(0, str(note.score))
        entry_score.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Date (YYYY-MM-DD):").pack(pady=5)
        entry_date = ctk.CTkEntry(edit_win)
        entry_date.insert(0, str(note.date))
        entry_date.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Coefficient:").pack(pady=5)
        entry_coeff = ctk.CTkEntry(edit_win)
        entry_coeff.insert(0, str(note.coefficient))
        entry_coeff.pack(pady=5)

        ctk.CTkLabel(edit_win, text="Subject:").pack(pady=5)
        subjects = self.session.query(Subject).join(Subject.followers).filter(User.id == self.current_user.id).all()
        subject_names = [s.name for s in subjects]
        subject_dropdown = ctk.CTkOptionMenu(edit_win, values=subject_names)
        subject_dropdown.set(note.subject.name if note.subject else subject_names[0])
        subject_dropdown.pack(pady=5)

        def save_changes():
            note.label = entry_label.get().strip()
            note.score = float(entry_score.get())
            from datetime import datetime
            note.date = datetime.strptime(entry_date.get(), "%Y-%m-%d").date()
            note.coefficient = float(entry_coeff.get())
            subject_name = subject_dropdown.get()
            subject = next((s for s in subjects if s.name == subject_name), None)
            if subject:
                note.subject_id = subject.id
            self.session.commit()
            edit_win.destroy()
            self.render_table()

        ctk.CTkButton(edit_win, text="Save", command=save_changes).pack(pady=20)
