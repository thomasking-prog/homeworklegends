# views/classroom_requests.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.join_request import JoinRequest, RequestStatus
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class ClassroomRequestWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Pending Requests")
        self.geometry("500x400")
        self.current_user = current_user
        self.session = Session()

        self.label = ctk.CTkLabel(self, text="Pending Join Requests")
        self.label.pack(pady=10)

        self.requests_frame = ctk.CTkFrame(self)
        self.requests_frame.pack(pady=10, fill="both", expand=True)

        self.load_requests()

    def load_requests(self):
        for widget in self.requests_frame.winfo_children():
            widget.destroy()

        if not self.current_user.classroom_id:
            ctk.CTkLabel(self.requests_frame, text="You are not assigned to any classroom").pack()
            return

        requests = (
            self.session.query(JoinRequest)
            .filter_by(status=RequestStatus.PENDING, classroom_id=self.current_user.classroom_id)
            .all()
        )

        if not requests:
            ctk.CTkLabel(self.requests_frame, text="No pending requests").pack()
            return

        for r in requests:
            user = r.user
            frame = ctk.CTkFrame(self.requests_frame)
            frame.pack(pady=5, fill="x", padx=10)

            text = f"{user.first_name} {user.last_name} ({user.username})"
            ctk.CTkLabel(frame, text=text).pack(side="left", padx=5)

            accept_btn = ctk.CTkButton(frame, text="Accept", fg_color="green", command=lambda rid=r.id: self.accept(rid))
            accept_btn.pack(side="right", padx=5)
            reject_btn = ctk.CTkButton(frame, text="Reject", fg_color="red", command=lambda rid=r.id: self.reject(rid))
            reject_btn.pack(side="right", padx=5)

    def accept(self, request_id):
        req = self.session.query(JoinRequest).get(request_id)
        if req:
            req.status = RequestStatus.ACCEPTED
            user = req.user
            user.classroom_id = req.classroom_id
            self.session.commit()
            self.load_requests()

    def reject(self, request_id):
        req = self.session.query(JoinRequest).get(request_id)
        if req:
            req.status = RequestStatus.REJECTED
            self.session.commit()
            self.load_requests()