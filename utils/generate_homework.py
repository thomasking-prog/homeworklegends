from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
import random

from config import DATABASE_URL
from models import Base, User, Subject, Homework, PriorityEnum

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter_by(username="admin").first()
subjects = user.subjects if user else []

today = date.today()
titles = [
    "Exercice Analyse", "Contrôle Calcul", "Révision Algèbre",
    "DM Statistiques", "Projet Géométrie", "QCM Logique",
    "Mini-test", "Correction Devoir 2", "Exercice maison", "TD intégrales"
]

for i in range(10):
    subject = random.choice(subjects)
    due = today - timedelta(days=random.randint(-10, 10))
    priority = random.choice(list(PriorityEnum))
    grade = round(random.uniform(5, 19), 1)

    hw = Homework(
        title=titles[i],
        description="Exercice auto-généré",
        due_date=due,
        priority=priority,
        user_id=user.id,
        subject_id=subject.id,
        grade=grade
    )
    session.add(hw)

session.commit()
print("✅ 10 devoirs générés (5 notés, 5 non notés)")