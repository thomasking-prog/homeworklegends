import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.subject import Subject
from models.user import User
from models.subject_follower import SubjectFollower
from models.classroom import Classroom
from functools import partial
from models.join_request import JoinRequest, RequestStatus
from utils.ranking import update_classroom_rank

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class ProfileView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.session = Session()

        db_user = self.session.query(User).get(self.current_user.id)

        # --- Header avec rang et couleur ---
        rank = db_user.rank
        rank_name = rank.name if rank else "Unranked"
        rank_color = rank.color if rank and rank.color else "#4287f5"
        elo = f"{int(db_user.rank_points)}" if db_user.rank_points is not None else "N/A"
        class_elo = f"{int(db_user.classroom.rank_points_avg)}" if db_user.classroom and db_user.classroom.rank_points_avg else "N/A"

        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=10, fill="x", padx=20)

        rank_label = ctk.CTkLabel(
            header_frame,
            text=f"🎖️ Rang personnel : {rank_name} ({elo} pts)",
            font=("Arial", 16, "bold"),
            text_color="white",
            fg_color=rank_color,
            corner_radius=10,
            width=300,
            height=40
        )
        rank_label.pack(side="left", padx=(0,20))

        if db_user.classroom:
            ctk.CTkLabel(
                header_frame,
                text=f"🏫 Classe : {db_user.classroom.name} — Moyenne Elo : {class_elo}",
                font=("Arial", 14)
            ).pack(side="left")

        # --- Gestion des classes ---
        class_frame = ctk.CTkFrame(self)
        class_frame.pack(pady=15, fill="x", padx=20)

        ctk.CTkLabel(class_frame, text="Classe actuelle:", font=("Arial", 14, "bold")).pack(anchor="w")
        self.current_class_label = ctk.CTkLabel(
            class_frame,
            text=db_user.classroom.name if db_user.classroom else "Aucune classe assignée"
        )
        self.current_class_label.pack(anchor="w", pady=(0, 10))

        self.leave_class_btn = ctk.CTkButton(
            class_frame,
            text="Quitter la classe",
            fg_color="red",
            command=self.leave_class
        )
        self.leave_class_btn.pack(anchor="w", pady=5)

        # --- Rejoindre une classe (placé dans le même frame) ---
        ctk.CTkLabel(class_frame, text="Rejoindre une classe", font=("Arial", 16, "bold")).pack(pady=(20, 5),
                                                                                                anchor="w")
        self.class_selector = ctk.CTkOptionMenu(class_frame, values=[], command=self.send_join_request)
        self.class_selector.pack(pady=5, anchor="w")

        self.join_status = ctk.CTkLabel(class_frame, text="")
        self.join_status.pack(pady=5, anchor="w")

        self.refresh_class_selector()

        # --- Matières suivies ---
        ctk.CTkLabel(self, text="Matières suivies", font=("Arial", 18)).pack(pady=10)
        self.subjects_frame = ctk.CTkScrollableFrame(self, height=200)
        self.subjects_frame.pack(fill="x", padx=10, pady=5)

        add_frame = ctk.CTkFrame(self)
        add_frame.pack(pady=20)

        ctk.CTkLabel(add_frame, text="Suivre une nouvelle matière :").pack()
        self.subject_selector = ctk.CTkOptionMenu(add_frame, values=[], command=self.follow_selected_subject)
        self.subject_selector.pack(pady=5)

        self.refresh_subjects()

    def refresh_class_selector(self):
        all_classes = self.session.query(Classroom).all()
        self.class_map = {c.name: c for c in all_classes}
        self.class_selector.configure(values=list(self.class_map.keys()))
        if all_classes:
            self.class_selector.set(all_classes[0].name)

    def leave_class(self):
        user = self.session.query(User).get(self.current_user.id)
        if user and user.classroom_id:
            old_classroom = user.classroom
            user.classroom_id = None
            update_classroom_rank(self.session, old_classroom)
            self.session.commit()
            self.refresh_profile()

    def send_join_request(self, class_name):
        classroom = self.class_map.get(class_name)
        if not classroom:
            self.join_status.configure(text="Classe invalide", text_color="red")
            return

        existing = self.session.query(JoinRequest).filter_by(
            user_id=self.current_user.id,
            classroom_id=classroom.id,
            status=RequestStatus.PENDING
        ).first()

        if existing:
            self.join_status.configure(text="Demande déjà en attente", text_color="orange")
            return

        if self.current_user.classroom_id == classroom.id:
            self.join_status.configure(text="Vous êtes déjà dans cette classe", text_color="blue")
            return

        request = JoinRequest(user_id=self.current_user.id, classroom_id=classroom.id)
        self.session.add(request)
        self.session.commit()
        self.join_status.configure(text="Demande envoyée avec succès", text_color="green")

    # --- Gestion des matières suivies ---
    def refresh_subjects(self):
        for widget in self.subjects_frame.winfo_children():
            widget.destroy()

        db_user = self.session.query(User).get(self.current_user.id)
        for subject in db_user.subjects:
            row = ctk.CTkFrame(self.subjects_frame)
            row.pack(pady=3, fill="x", padx=5)

            label = ctk.CTkLabel(row, text=subject.name)
            label.pack(side="left", padx=5)

            btn = ctk.CTkButton(row, text="Ne plus suivre", fg_color="red", command=partial(self.unfollow, subject))
            btn.pack(side="right", padx=5)

        self.update_subject_selector()

    def update_subject_selector(self):
        db_user = self.session.query(User).get(self.current_user.id)
        followed_ids = {s.id for s in db_user.subjects}
        all_subjects = self.session.query(Subject).all()
        unfollowed = [s.name for s in all_subjects if s.id not in followed_ids]

        if unfollowed:
            self.subject_selector.configure(values=unfollowed, state="normal")
            self.subject_selector.set(unfollowed[0])
        else:
            self.subject_selector.configure(values=["Aucune matière disponible"], state="disabled")

    def follow_selected_subject(self, subject_name):
        subject = self.session.query(Subject).filter_by(name=subject_name).first()
        if subject:
            user = self.session.query(User).get(self.current_user.id)
            exists = any(link.subject_id == subject.id for link in user.subject_links)
            if not exists:
                link = SubjectFollower(user_id=user.id, subject_id=subject.id)
                self.session.add(link)
                self.session.commit()
            self.refresh_subjects()

    def unfollow(self, subject):
        user = self.session.query(User).get(self.current_user.id)
        link = next((l for l in user.subject_links if l.subject_id == subject.id), None)
        if link:
            self.session.delete(link)
            self.session.commit()
            self.session.refresh(user)
        self.refresh_subjects()

    def refresh_profile(self):
        # Recharge l'utilisateur en base
        db_user = self.session.query(User).get(self.current_user.id)

        # Met à jour label de la classe actuelle
        if db_user.classroom:
            self.current_class_label.configure(text=db_user.classroom.name)
        else:
            self.current_class_label.configure(text="Aucune classe assignée")

        # Mets à jour le label rang perso (si tu en as un affiché)
        rank = db_user.rank
        rank_name = rank.name if rank else "Unranked"
        rank_color = rank.color if rank and rank.color else "#4287f5"
        elo = f"{int(db_user.rank_points)}" if db_user.rank_points is not None else "N/A"

        # Supposons que tu aies un label self.rank_label (sinon crée-le dans __init__)
        if hasattr(self, 'rank_label'):
            self.rank_label.configure(
                text=f"🎖️ Rang personnel : {rank_name} ({elo} pts)",
                fg_color=rank_color
            )

        # Mets à jour les matières suivies
        self.refresh_subjects()

        # Mets à jour la liste des classes disponibles dans le sélecteur
        self.refresh_class_selector()



