from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, RoleEnum, Subject, SubjectFollower, Rank
from models.classroom import Classroom
from config import DATABASE_URL
import bcrypt

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("✅ Database tables created.")

    Session = sessionmaker(bind=engine)
    session = Session()

    admin_exists = session.query(User).filter(User.role == RoleEnum.ADMIN).first()
    if not admin_exists:
        # ✅ Créer les rangs
        ranks = [
            {"name": "Bronze", "min": 0, "max": 2000, "color": "#cd7f32"},
            {"name": "Argent", "min": 2000, "max": 2300, "color": "#c0c0c0"},
            {"name": "Or", "min": 2300, "max": 2600, "color": "#ffd700"},
            {"name": "Platine", "min": 2600, "max": 2900, "color": "#0bb5ff"},
            {"name": "Diamant", "min": 2900, "max": 3200, "color": "#b9f2ff"},
            {"name": "Maître", "min": 3200, "max": None, "color": "#800080"},
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

        # ✅ Créer des classes
        class_a = Classroom(name="Classe A", description="Classe principale")
        class_b = Classroom(name="Classe B", description="Classe secondaire")
        session.add_all([class_a, class_b])

        # ✅ Créer l'utilisateur admin
        hashed_pw = bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        admin = User(
            first_name="Admin",
            last_name="User",
            username="admin",
            password=hashed_pw,
            role=RoleEnum.ADMIN,
            rank_id=1,  # Bronze par défaut
            rank_points=1000,
            classroom=class_a
        )
        session.add(admin)

        # ✅ Créer les matières
        math = Subject(name="Math")
        fr = Subject(name="FR")
        session.add_all([math, fr])

        session.flush()  # ➕ Génère les IDs de admin/math/fr

        # ✅ Suivi des matières par admin
        follow_math = SubjectFollower(user_id=admin.id, subject_id=math.id)
        follow_fr = SubjectFollower(user_id=admin.id, subject_id=fr.id)
        session.add_all([follow_math, follow_fr])

        # ✅ Commit final
        session.commit()
        print("✅ Default admin user, subjects, ranks, and classrooms created.")
    else:
        print("ℹ️ Admin user already exists.")

    session.close()

if __name__ == "__main__":
    init_db()