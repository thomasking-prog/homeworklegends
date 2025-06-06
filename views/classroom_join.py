# views/classroom_join.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.classroom import Classroom
from models.join_request import JoinRequest, RequestStatus
from models.user import User

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class ClassroomJoinWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Join Classroom")
        self.geometry("400x400")
        self.current_user = current_user

        self.session = Session()

        self.label = ctk.CTkLabel(self, text="Available Classrooms:")
        self.label.pack(pady=10)

        self.class_listbox = ctk.CTkComboBox(self, values=[])
        self.class_listbox.pack(pady=10)

        self.btn_request = ctk.CTkButton(self, text="Request to Join", command=self.request_join)
        self.btn_request.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=10)

        self.load_classrooms()

    def load_classrooms(self):
        classrooms = self.session.query(Classroom).all()
        self.class_listbox.configure(values=[c.name for c in classrooms])
        self.classrooms = classrooms

    def request_join(self):
        selected_name = self.class_listbox.get()
        classroom = next((c for c in self.classrooms if c.name == selected_name), None)
        if classroom is None:
            self.status_label.configure(text="Please select a classroom", text_color="red")
            return

        # Check if already requested or member
        existing_request = self.session.query(JoinRequest).filter_by(
            user_id=self.current_user.id,
            classroom_id=classroom.id,
            status=RequestStatus.PENDING
        ).first()
        if existing_request:
            self.status_label.configure(text="Request already pending", text_color="red")
            return

        if self.current_user.classroom_id == classroom.id:
            self.status_label.configure(text="You are already a member", text_color="red")
            return

        # Create join request
        join_request = JoinRequest(user_id=self.current_user.id, classroom_id=classroom.id)
        self.session.add(join_request)
        self.session.commit()
        self.status_label.configure(text="Request sent", text_color="green")