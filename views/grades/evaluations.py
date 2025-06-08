import customtkinter as ctk
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from utils.ranking import update_user_score, remove_user_score
from utils.scoring import apply_score_update
from models.evaluation_note import EvaluationNote
from models.user import User
from models.subject import Subject

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class EvaluationView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.session = Session()

        # === Frame filtre + tableau ===
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.filters_frame = ctk.CTkFrame(self.list_frame)
        self.filters_frame.pack(fill="x", pady=5)

        self.filter_label = ctk.CTkEntry(self.filters_frame, placeholder_text="Filter by label...")
        self.filter_label.pack(side="left", padx=5)

        self.subjects = self.session.query(Subject).join(Subject.followers).filter(User.id == self.current_user.id).all()
        subject_names = [s.name for s in self.subjects]
        self.subject_filter = ctk.CTkOptionMenu(self.filters_frame, values=["All"] + subject_names)
        self.subject_filter.set("All")
        self.subject_filter.pack(side="left", padx=5)

        self.apply_filter_btn = ctk.CTkButton(self.filters_frame, text="Apply Filters", command=self.render_table)
        self.apply_filter_btn.pack(side="left", padx=5)

        self.table_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.table_frame.pack(fill="both", expand=True)

        # === Frame formulaire création ===
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(padx=10, pady=10)
        self.form_frame.configure(width=400, height=350)
        self.form_frame.pack_propagate(False)

        # Form fields
        self.label_label = ctk.CTkLabel(self.form_frame, text="Label:")
        self.label_label.grid(row=0, column=0, sticky="w", pady=5)
        self.entry_label = ctk.CTkEntry(self.form_frame)
        self.entry_label.grid(row=0, column=1, sticky="ew", pady=5)

        self.label_score = ctk.CTkLabel(self.form_frame, text="Score (0-20):")
        self.label_score.grid(row=1, column=0, sticky="w", pady=5)
        self.entry_score = ctk.CTkEntry(self.form_frame)
        self.entry_score.grid(row=1, column=1, sticky="ew", pady=5)

        self.label_date = ctk.CTkLabel(self.form_frame, text="Date (YYYY-MM-DD):")
        self.label_date.grid(row=2, column=0, sticky="w", pady=5)
        self.entry_date = ctk.CTkEntry(self.form_frame)
        self.entry_date.grid(row=2, column=1, sticky="ew", pady=5)

        self.label_coeff = ctk.CTkLabel(self.form_frame, text="Coefficient (default 1):")
        self.label_coeff.grid(row=3, column=0, sticky="w", pady=5)
        self.entry_coeff = ctk.CTkEntry(self.form_frame)
        self.entry_coeff.grid(row=3, column=1, sticky="ew", pady=5)
        self.entry_coeff.insert(0, "1")

        self.label_subject = ctk.CTkLabel(self.form_frame, text="Subject:")
        self.label_subject.grid(row=4, column=0, sticky="w", pady=5)
        self.subject_box = ctk.CTkComboBox(self.form_frame, values=subject_names)
        self.subject_box.grid(row=4, column=1, sticky="ew", pady=5)

        self.status_label = ctk.CTkLabel(self.form_frame, text="")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=10)

        self.btn_submit = ctk.CTkButton(self.form_frame, text="Add Evaluation", command=self.submit)
        self.btn_submit.grid(row=6, column=0, columnspan=2, pady=10)

        self.form_frame.columnconfigure(1, weight=1)

        self.render_table()

    def render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = ["Date", "Label", "Subject", "Score (/20)", "Coefficient", "Actions"]
        for col, title in enumerate(headers):
            header = ctk.CTkLabel(self.table_frame, text=title, font=("Arial", 13, "bold"))
            header.grid(row=0, column=col, padx=1, pady=2, sticky="nsew")

        query = self.session.query(EvaluationNote).filter_by(user_id=self.current_user.id)

        label_filter = self.filter_label.get().strip().lower()
        if label_filter:
            query = query.filter(EvaluationNote.label.ilike(f"%{label_filter}%"))

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
            user = self.session.query(User).get(self.current_user.id)

            # Retirer l’impact de la note avant suppression
            remove_user_score(self.session, user, note.score)

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
            user = self.session.query(User).get(self.current_user.id)

            old_score = note.score
            new_score = float(entry_score.get())

            # Met à jour score + rank proprement
            update_user_score(self.session, user, old_score, new_score)

            # Modifie l'évaluation
            note.label = entry_label.get().strip()
            note.score = new_score
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

    def submit(self):
        try:
            label = self.entry_label.get().strip()
            score = float(self.entry_score.get())
            date = datetime.strptime(self.entry_date.get(), "%Y-%m-%d").date()
            coeff = float(self.entry_coeff.get() or 1)
            subject_name = self.subject_box.get()

            if not label or not subject_name:
                raise ValueError("Missing data")

            subject = next((s for s in self.subjects if s.name == subject_name), None)
            if not subject:
                raise ValueError("Invalid subject")

            note = EvaluationNote(
                label=label,
                score=score,
                date=date,
                coefficient=coeff,
                user_id=self.current_user.id,
                subject_id=subject.id
            )
            self.session.add(note)
            self.session.flush()  # Génère l'ID et synchronise la session

            user = self.session.query(User).get(self.current_user.id)

            # Applique l'impact du nouveau score
            apply_score_update(self.session, user, score)

            self.session.commit()
            self.session.refresh(user)

            self.status_label.configure(text="Evaluation added!", text_color="green")
            self.entry_label.delete(0, "end")
            self.entry_score.delete(0, "end")
            self.entry_date.delete(0, "end")
            self.entry_coeff.delete(0, "end")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")

