import customtkinter as ctk
from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.join_request import JoinRequest, RequestStatus
from utils.ranking import update_classroom_rank
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class DelegateView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.session = Session()

        ctk.CTkLabel(self, text="Demandes de rejoindre la classe", font=("Arial", 20)).pack(pady=10)

        self.requests_frame = ctk.CTkScrollableFrame(self)
        self.requests_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_requests()

    def load_requests(self):
        for widget in self.requests_frame.winfo_children():
            widget.destroy()

        # S'assurer que l'utilisateur est bien délégué d'une classe
        if not self.current_user.classroom_id:
            ctk.CTkLabel(self.requests_frame, text="Aucune classe assignée.").pack(pady=10)
            return

        requests = (
            self.session.query(JoinRequest)
            .filter_by(status=RequestStatus.PENDING, classroom_id=self.current_user.classroom_id)
            .all()
        )

        if not requests:
            ctk.CTkLabel(self.requests_frame, text="Aucune demande en attente").pack(pady=10)
            return

        for r in requests:
            user = r.user
            row = ctk.CTkFrame(self.requests_frame)
            row.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(row, text=f"{user.first_name} {user.last_name} ({user.username})").pack(side="left", padx=10)

            btn_accept = ctk.CTkButton(row, text="Accepter", fg_color="green", width=80,
                                       command=partial(self.respond_request, r, True))
            btn_accept.pack(side="right", padx=5)

            btn_reject = ctk.CTkButton(row, text="Refuser", fg_color="red", width=80,
                                       command=partial(self.respond_request, r, False))
            btn_reject.pack(side="right", padx=5)

    def respond_request(self, request, accept):
        if accept:
            request.status = RequestStatus.ACCEPTED
            user = request.user
            user.classroom_id = request.classroom_id

            classroom = request.classroom
            update_classroom_rank(self.session, classroom)

        else:
            request.status = RequestStatus.REJECTED

        self.session.commit()
        self.load_requests()
