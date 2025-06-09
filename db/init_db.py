from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, RoleEnum, Subject, SubjectFollower, Rank
from models.classroom import Classroom
from models.evaluation_note import EvaluationNote
from config import DATABASE_URL
import bcrypt
import random
from datetime import date, timedelta
from models.homework import Homework, PriorityEnum
from utils import update_averages

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("✅ Database tables created.")

    Session = sessionmaker(bind=engine)
    session = Session()

    ranks = [
        {"name": "Bronze", "min": 0, "max": 1999, "color": "#cd7f32"},
        {"name": "Argent", "min": 2000, "max": 2499, "color": "#c0c0c0"},
        {"name": "Or", "min": 2500, "max": 2999, "color": "#ffd700"},
        {"name": "Platine", "min": 3000, "max": 3499, "color": "#00bfff"},
        {"name": "Diamant", "min": 3500, "max": None, "color": "#b9f2ff"},
    ]

    for order, data in enumerate(ranks, start=1):
        exists = session.query(Rank).filter_by(name=data["name"]).first()
        if not exists:
            rank = Rank(
                name=data["name"],
                min_points=data["min"],
                max_points=data["max"],
                order=order,
                color=data["color"]
            )
            session.add(rank)

    session.flush()

    rank_platine = session.query(Rank).filter_by(name="Platine").first()
    rank_or = session.query(Rank).filter_by(name="Or").first()
    rank_bronze = session.query(Rank).filter_by(name="Bronze").first()

    class_alpha = Classroom(
        name="Classe Alpha",
        description="Classe expérimentée",
        rank_points_avg=2800,
        rank=rank_platine
    )

    class_beta = Classroom(
        name="Classe Beta",
        description="Classe intermédiaire",
        rank_points_avg=2400,
        rank=rank_or
    )

    class_gamma = Classroom(
        name="Classe Gamma",
        description="Nouvelle promotion",
        rank_points_avg=1800,
        rank=rank_bronze
    )

    session.add_all([class_alpha, class_beta, class_gamma])
    session.flush()

    subjects = [
        "Mathématiques",
        "Français",
        "Histoire-Géographie",
        "Sciences de la Vie",
        "Physique-Chimie",
        "Anglais",
        "Philosophie",
        "Informatique"
    ]

    for name in subjects:
        exists = session.query(Subject).filter_by(name=name).first()
        if not exists:
            subject = Subject(name=name)
            session.add(subject)

    session.flush()

    classes = session.query(Classroom).all()
    rank_bronze = session.query(Rank).filter_by(name="Bronze").first()

    first_names = [
        "Alice", "Bob", "Charlie", "Diane", "Ethan", "Fiona", "Gaspard", "Hana",
        "Ismael", "Julia", "Kevin", "Lina", "Marc", "Nora", "Oscar", "Paul",
        "Quentin", "Rosa", "Sophie", "Tom"
    ]

    last_names = [
        "Durand", "Martin", "Bernard", "Petit", "Moreau", "Garcia", "Roux",
        "Lambert", "Blanc", "Dupuis",
        "Lemoine", "Marchand", "Faure", "Gautier", "Chevalier", "Leroy",
        "Colin", "Vidal"
    ]

    for classroom in classes:
        delegate_fn = first_names.pop(0)
        delegate_ln = last_names.pop(0)
        delegate_username = f"{delegate_fn.lower()}.{delegate_ln.lower()}"
        delegate_pw = bcrypt.hashpw("password".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        delegate = User(
            first_name=delegate_fn,
            last_name=delegate_ln,
            username=delegate_username,
            password=delegate_pw,
            role=RoleEnum.DELEGATE,
            classroom=classroom,
            rank_id=rank_bronze.id,
            rank_points=1100
        )
        session.add(delegate)

        for _ in range(5):
            fn = first_names.pop(0)
            ln = last_names.pop(0)
            username = f"{fn.lower()}.{ln.lower()}"
            pw = bcrypt.hashpw("password".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            student = User(
                first_name=fn,
                last_name=ln,
                username=username,
                password=pw,
                role=RoleEnum.STUDENT,
                classroom=classroom,
                rank_id=rank_bronze.id,
                rank_points=1000
            )
            session.add(student)

    session.flush()

    users = session.query(User).filter(User.role.in_([RoleEnum.STUDENT, RoleEnum.DELEGATE])).all()
    subjects = session.query(Subject).all()

    for user in users:
        followed_subjects = random.sample(subjects, k=5)
        for subject in followed_subjects:
            follower = SubjectFollower(
                user_id=user.id,
                subject_id=subject.id,
                average=None
            )
            session.add(follower)

    session.flush()

    # Ajouter 10 évaluations par utilisateur, réparties parmi les matières suivies
    for user in users:
        subject_followers = session.query(SubjectFollower).filter_by(user_id=user.id).all()
        followed_subject_ids = [sf.subject_id for sf in subject_followers]

        for i in range(10):
            subject_id = random.choice(followed_subject_ids)
            subject = session.get(Subject, subject_id)


            evaluation = EvaluationNote(
                label=f"Évaluation {i + 1} - {subject.name}",
                score=round(random.uniform(8.0, 20.0), 2),
                date=date.today() - timedelta(days=random.randint(10, 180)),
                coefficient=random.choice([1.0, 1.5, 2.0]),
                user_id=user.id,
                subject_id=subject_id
            )
            session.add(evaluation)

    session.flush()

    priorities = [PriorityEnum.LOW, PriorityEnum.MEDIUM, PriorityEnum.HIGH]

    for user in users:
        # Récupérer les matières suivies par cet utilisateur
        followed_subjects = session.query(Subject).join(SubjectFollower).filter(
            SubjectFollower.user_id == user.id).all()

        # Créer 5 devoirs répartis sur les matières suivies
        for i in range(5):
            subject = random.choice(followed_subjects)

            # Dates d'échéance réparties dans les 30 prochains jours
            due_date = date.today() + timedelta(days=random.randint(1, 30))

            # Priorité aléatoire
            priority = random.choice(priorities)

            # Grade aléatoire ou None (50% chance)
            grade = random.uniform(0, 20) if random.random() > 0.5 else None

            hw = Homework(
                title=f"Devoir {i + 1} - {subject.name}",
                description=f"Travail à rendre pour la matière {subject.name}",
                due_date=due_date,
                priority=priority,
                grade=grade,
                user_id=user.id,
                subject_id=subject.id
            )
            session.add(hw)

    session.flush()

    update_averages(session)

    session.commit()
    session.close()

if __name__ == "__main__":
    init_db()
