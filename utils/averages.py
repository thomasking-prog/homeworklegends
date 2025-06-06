# utils/averages.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import User, Homework, EvaluationNote, SubjectFollower
from utils.ranking import update_rank_points, update_user_rank

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def update_subject_averages(session, user):
    for link in user.subject_links:
        subject_id = link.subject_id

        # Récupérer toutes les évaluations de cette matière pour l'utilisateur
        evaluations = session.query(EvaluationNote).filter_by(user_id=user.id, subject_id=subject_id).all()
        # Récupérer toutes les notes de devoirs notés
        homeworks = session.query(Homework).filter(
            Homework.user_id == user.id,
            Homework.subject_id == subject_id,
            Homework.grade != None
        ).all()

        total_points = 0
        total_coeff = 0

        for ev in evaluations:
            total_points += ev.score * ev.coefficient
            total_coeff += ev.coefficient

        for hw in homeworks:
            total_points += hw.grade  # coefficient 1
            total_coeff += 1

        if total_coeff > 0:
            link.average = total_points / total_coeff
        else:
            link.average = None

def update_user_global_average(session, user):
    update_subject_averages(session, user)

    total = 0
    count = 0
    for link in user.subject_links:
        if link.average is not None:
            total += link.average
            count += 1

    user.global_average = total / count if count > 0 else None