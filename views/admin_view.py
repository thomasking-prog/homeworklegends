import customtkinter as ctk
from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.classroom import Classroom
from models.subject import Subject
from models.join_request import JoinRequest, RequestStatus
from models.user import User, RoleEnum
from utils.ranking import update_classroom_rank
import bcrypt

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class AdminView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.session = Session()

        ctk.CTkLabel(self, text="Admin Panel", font=("Arial", 24)).pack(pady=20)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Ajout des onglets
        self.tabview.add("Classrooms")
        self.tabview.add("Subjects")
        self.tabview.add("Join Requests")
        self.tabview.add("Users")

        # === Onglet Classrooms ===
        self.classrooms_frame = ctk.CTkScrollableFrame(self.tabview.tab("Classrooms"))
        self.classrooms_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._init_classrooms_tab()

        # === Onglet Subjects ===
        self.subjects_frame = ctk.CTkScrollableFrame(self.tabview.tab("Subjects"))
        self.subjects_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._init_subjects_tab()

        # === Onglet Join Requests ===
        self.requests_frame = ctk.CTkScrollableFrame(self.tabview.tab("Join Requests"))
        self.requests_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._init_requests_tab()

        # === Onglet Users ===
        self.users_frame = ctk.CTkScrollableFrame(self.tabview.tab("Users"))
        self.users_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._init_users_tab()


    # ======== CLASSROOMS =========

    def _init_classrooms_tab(self):
        form_frame = ctk.CTkFrame(self.classrooms_frame)
        form_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(form_frame, text="Classroom Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_classroom_name = ctk.CTkEntry(form_frame)
        self.entry_classroom_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Description:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_classroom_desc = ctk.CTkEntry(form_frame)
        self.entry_classroom_desc.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        form_frame.grid_columnconfigure(1, weight=1)

        self.classroom_status_label = ctk.CTkLabel(form_frame, text="")
        self.classroom_status_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.btn_submit_classroom = ctk.CTkButton(form_frame, text="Create Classroom", command=self.create_or_update_classroom)
        self.btn_submit_classroom.grid(row=3, column=0, columnspan=2, pady=10)

        self.classroom_list_frame = ctk.CTkScrollableFrame(self.classrooms_frame)
        self.classroom_list_frame.pack(fill="both", expand=True, pady=10)

        self.editing_classroom = None
        self.load_classrooms()

    def create_or_update_classroom(self):
        name = self.entry_classroom_name.get().strip()
        desc = self.entry_classroom_desc.get().strip()

        if not name:
            self.classroom_status_label.configure(text="Name is required", text_color="red")
            return

        if self.editing_classroom is None:
            # Création
            if self.session.query(Classroom).filter_by(name=name).first():
                self.classroom_status_label.configure(text="Classroom already exists", text_color="red")
                return

            classroom = Classroom(name=name, description=desc)
            self.session.add(classroom)
            self.session.commit()

            self.classroom_status_label.configure(text="Classroom created!", text_color="green")
        else:
            # Edition
            existing = self.session.query(Classroom).filter(Classroom.name == name, Classroom.id != self.editing_classroom.id).first()
            if existing:
                self.classroom_status_label.configure(text="Another classroom with this name exists", text_color="red")
                return

            self.editing_classroom.name = name
            self.editing_classroom.description = desc
            self.session.commit()

            self.classroom_status_label.configure(text="Classroom updated!", text_color="green")

            self.editing_classroom = None
            self.btn_submit_classroom.configure(text="Create Classroom")

        self.entry_classroom_name.delete(0, "end")
        self.entry_classroom_desc.delete(0, "end")
        self.load_classrooms()

    def load_classrooms(self):
        for w in self.classroom_list_frame.winfo_children():
            w.destroy()

        classrooms = self.session.query(Classroom).all()
        for c in classrooms:
            row = ctk.CTkFrame(self.classroom_list_frame)
            row.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(row, text=c.name, width=200).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=c.description or "", width=300).pack(side="left", padx=10)

            btn_edit = ctk.CTkButton(row, text="Edit", width=80, command=partial(self.start_edit_classroom, c))
            btn_edit.pack(side="right", padx=5)
            btn_del = ctk.CTkButton(row, text="Delete", fg_color="red", width=80, command=partial(self.delete_classroom, c))
            btn_del.pack(side="right", padx=5)

    def start_edit_classroom(self, classroom):
        self.editing_classroom = classroom
        self.entry_classroom_name.delete(0, "end")
        self.entry_classroom_name.insert(0, classroom.name)
        self.entry_classroom_desc.delete(0, "end")
        self.entry_classroom_desc.insert(0, classroom.description or "")
        self.btn_submit_classroom.configure(text="Save Changes")
        self.classroom_status_label.configure(text="Editing classroom...")

    def delete_classroom(self, classroom):
        self.session.delete(self.session.merge(classroom))
        self.session.commit()
        if self.editing_classroom == classroom:
            self.editing_classroom = None
            self.btn_submit_classroom.configure(text="Create Classroom")
            self.entry_classroom_name.delete(0, "end")
            self.entry_classroom_desc.delete(0, "end")
            self.classroom_status_label.configure(text="")
        self.load_classrooms()


    # ======== SUBJECTS =========

    def _init_subjects_tab(self):
        form_frame = ctk.CTkFrame(self.subjects_frame)
        form_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(form_frame, text="Subject Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_subject_name = ctk.CTkEntry(form_frame)
        self.entry_subject_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        form_frame.grid_columnconfigure(1, weight=1)

        self.subject_status_label = ctk.CTkLabel(form_frame, text="")
        self.subject_status_label.grid(row=1, column=0, columnspan=2, pady=5)

        self.btn_submit_subject = ctk.CTkButton(form_frame, text="Add Subject", command=self.create_or_update_subject)
        self.btn_submit_subject.grid(row=2, column=0, columnspan=2, pady=10)

        self.subject_list_frame = ctk.CTkScrollableFrame(self.subjects_frame)
        self.subject_list_frame.pack(fill="both", expand=True, pady=10)

        self.editing_subject = None
        self.load_subjects()

    def create_or_update_subject(self):
        name = self.entry_subject_name.get().strip()

        if not name:
            self.subject_status_label.configure(text="Name is required", text_color="red")
            return

        if self.editing_subject is None:
            # Création
            if self.session.query(Subject).filter_by(name=name).first():
                self.subject_status_label.configure(text="Subject already exists", text_color="red")
                return

            subject = Subject(name=name)
            self.session.add(subject)
            self.session.commit()

            self.subject_status_label.configure(text="Subject created!", text_color="green")
        else:
            # Edition
            existing = self.session.query(Subject).filter(Subject.name == name, Subject.id != self.editing_subject.id).first()
            if existing:
                self.subject_status_label.configure(text="Another subject with this name exists", text_color="red")
                return

            self.editing_subject.name = name
            self.session.commit()

            self.subject_status_label.configure(text="Subject updated!", text_color="green")

            self.editing_subject = None
            self.btn_submit_subject.configure(text="Add Subject")

        self.entry_subject_name.delete(0, "end")
        self.load_subjects()

    def load_subjects(self):
        for w in self.subject_list_frame.winfo_children():
            w.destroy()

        subjects = self.session.query(Subject).all()
        for s in subjects:
            row = ctk.CTkFrame(self.subject_list_frame)
            row.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(row, text=s.name, width=200).pack(side="left", padx=10)

            btn_edit = ctk.CTkButton(row, text="Edit", width=80, command=partial(self.start_edit_subject, s))
            btn_edit.pack(side="right", padx=5)

            btn_del = ctk.CTkButton(row, text="Delete", fg_color="red", width=80, command=partial(self.delete_subject, s))
            btn_del.pack(side="right", padx=5)

    def start_edit_subject(self, subject):
        self.editing_subject = subject
        self.entry_subject_name.delete(0, "end")
        self.entry_subject_name.insert(0, subject.name)
        self.btn_submit_subject.configure(text="Save Changes")
        self.subject_status_label.configure(text="Editing subject...")

    def delete_subject(self, subject):
        self.session.delete(self.session.merge(subject))
        self.session.commit()
        if self.editing_subject == subject:
            self.editing_subject = None
            self.btn_submit_subject.configure(text="Add Subject")
            self.entry_subject_name.delete(0, "end")
            self.subject_status_label.configure(text="")
        self.load_subjects()


    # ======== JOIN REQUESTS ========

    def _init_requests_tab(self):
        self.requests_list_frame = ctk.CTkScrollableFrame(self.requests_frame)
        self.requests_list_frame.pack(fill="both", expand=True)

        self.load_requests()

    def load_requests(self):
        for w in self.requests_list_frame.winfo_children():
            w.destroy()

        requests = self.session.query(JoinRequest).filter(JoinRequest.status == RequestStatus.PENDING).all()
        if not requests:
            ctk.CTkLabel(self.requests_list_frame, text="No pending requests").pack(pady=20)
            return

        for req in requests:
            row = ctk.CTkFrame(self.requests_list_frame)
            row.pack(fill="x", pady=5, padx=5)

            user = req.user
            classroom = req.classroom

            ctk.CTkLabel(row, text=f"{user.first_name} {user.last_name} ({user.username})").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"Requested to join: {classroom.name}").pack(side="left", padx=10)

            btn_accept = ctk.CTkButton(row, text="Accept", fg_color="green", width=80, command=partial(self.respond_request, req, True))
            btn_accept.pack(side="right", padx=5)

            btn_reject = ctk.CTkButton(row, text="Reject", fg_color="red", width=80, command=partial(self.respond_request, req, False))
            btn_reject.pack(side="right", padx=5)

    def respond_request(self, request, accept: bool):
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


    # ======== USERS ===========

    def _init_users_tab(self):
        form_frame = ctk.CTkFrame(self.users_frame)
        form_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(form_frame, text="First Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_user_first_name = ctk.CTkEntry(form_frame)
        self.entry_user_first_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Last Name:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_user_last_name = ctk.CTkEntry(form_frame)
        self.entry_user_last_name.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Username:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_user_username = ctk.CTkEntry(form_frame)
        self.entry_user_username.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Password:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_user_password = ctk.CTkEntry(form_frame, show="*")
        self.entry_user_password.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Role:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        roles = [r.value for r in RoleEnum]
        self.user_role_menu = ctk.CTkOptionMenu(form_frame, values=roles)
        self.user_role_menu.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.user_role_menu.set(RoleEnum.STUDENT.value)

        form_frame.grid_columnconfigure(1, weight=1)

        self.user_status_label = ctk.CTkLabel(form_frame, text="")
        self.user_status_label.grid(row=5, column=0, columnspan=2, pady=5)

        self.btn_submit_user = ctk.CTkButton(form_frame, text="Create User", command=self.create_or_update_user)
        self.btn_submit_user.grid(row=6, column=0, columnspan=2, pady=10)

        self.user_list_frame = ctk.CTkScrollableFrame(self.users_frame)
        self.user_list_frame.pack(fill="both", expand=True, pady=10)

        self.editing_user = None
        self.load_users()

    def create_or_update_user(self):
        first_name = self.entry_user_first_name.get().strip()
        last_name = self.entry_user_last_name.get().strip()
        username = self.entry_user_username.get().strip()
        password = self.entry_user_password.get()
        role_value = self.user_role_menu.get()

        if not (first_name and last_name and username):
            self.user_status_label.configure(text="First name, last name, and username are required", text_color="red")
            return

        if self.editing_user is None:
            # Création
            if self.session.query(User).filter_by(username=username).first():
                self.user_status_label.configure(text="Username already exists", text_color="red")
                return

            if not password:
                self.user_status_label.configure(text="Password is required for new user", text_color="red")
                return

            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                password=hashed_pw,
                role=RoleEnum(role_value)
            )
            self.session.add(user)
            self.session.commit()

            self.user_status_label.configure(text="User created!", text_color="green")

        else:
            # Edition
            existing = self.session.query(User).filter(User.username == username, User.id != self.editing_user.id).first()
            if existing:
                self.user_status_label.configure(text="Another user with this username exists", text_color="red")
                return

            self.editing_user.first_name = first_name
            self.editing_user.last_name = last_name
            self.editing_user.username = username
            self.editing_user.role = RoleEnum(role_value)

            if password:
                hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                self.editing_user.password = hashed_pw

            self.session.commit()
            self.user_status_label.configure(text="User updated!", text_color="green")

            self.editing_user = None
            self.btn_submit_user.configure(text="Create User")

        self.entry_user_first_name.delete(0, "end")
        self.entry_user_last_name.delete(0, "end")
        self.entry_user_username.delete(0, "end")
        self.entry_user_password.delete(0, "end")
        self.user_role_menu.set(RoleEnum.STUDENT.value)

        self.load_users()

    def load_users(self):
        for w in self.user_list_frame.winfo_children():
            w.destroy()

        users = self.session.query(User).all()
        for user in users:
            row = ctk.CTkFrame(self.user_list_frame)
            row.pack(fill="x", pady=5, padx=5)

            name = f"{user.first_name} {user.last_name}"
            ctk.CTkLabel(row, text=name, width=200).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=user.username, width=150).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=user.role.value, width=100).pack(side="left", padx=10)

            btn_edit = ctk.CTkButton(row, text="Edit", width=80, command=partial(self.start_edit_user, user))
            btn_edit.pack(side="right", padx=5)

            btn_del = ctk.CTkButton(row, text="Delete", fg_color="red", width=80, command=partial(self.delete_user, user))
            btn_del.pack(side="right", padx=5)

    def start_edit_user(self, user):
        self.editing_user = user
        self.entry_user_first_name.delete(0, "end")
        self.entry_user_first_name.insert(0, user.first_name)
        self.entry_user_last_name.delete(0, "end")
        self.entry_user_last_name.insert(0, user.last_name)
        self.entry_user_username.delete(0, "end")
        self.entry_user_username.insert(0, user.username)
        self.entry_user_password.delete(0, "end")
        self.user_role_menu.set(user.role.value)
        self.btn_submit_user.configure(text="Save Changes")
        self.user_status_label.configure(text="Editing user...")

    def delete_user(self, user):
        self.session.delete(self.session.merge(user))
        self.session.commit()
        if self.editing_user == user:
            self.editing_user = None
            self.btn_submit_user.configure(text="Create User")
            self.entry_user_first_name.delete(0, "end")
            self.entry_user_last_name.delete(0, "end")
            self.entry_user_username.delete(0, "end")
            self.entry_user_password.delete(0, "end")
            self.user_role_menu.set(RoleEnum.STUDENT.value)
            self.user_status_label.configure(text="")
        self.load_users()
