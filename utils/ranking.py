from models.rank import Rank
from models.user import User
from models.classroom import Classroom

def update_user_rank(session, user):
    ranks = session.query(Rank).order_by(Rank.order).all()
    for rank in ranks:
        if rank.max_points is None:
            if user.rank_points >= rank.min_points:
                user.rank = rank
                break
        else:
            if rank.min_points <= user.rank_points < rank.max_points:
                user.rank = rank
                break
    if user.classroom is None:
        return

    update_classroom_rank(session, user.classroom)

def update_rank_points(user, new_score):
    user.rank_points += calculate_delta(user, new_score)

def calculate_expected(user):
    elo_min = user.rank.min_points
    elo_max = user.rank.max_points if user.rank.max_points is not None else user.rank_points + 1  # éviter division par 0

    # Clamp l'ELO dans la plage
    points = max(elo_min, min(elo_max, user.rank_points))

    # Si les deux bornes sont égales (rare mais possible), retourner max
    if elo_max == elo_min:
        return 0.8

    # Interpolation linéaire de 0.4 à 0.8
    expected = 0.4 + (points - elo_min) / (elo_max - elo_min) * 0.4
    return expected


def update_classroom_rank(session, classroom):
    users = classroom.users
    if not users:
        classroom.rank_points_avg = None
        classroom.rank_id = None
        return

    total = 0
    count = 0
    for user in users:
        if user.rank_points is not None:
            total += user.rank_points
            count += 1

    if count == 0:
        classroom.rank_points_avg = None
        classroom.rank_id = None
    else:
        avg = total / count
        classroom.rank_points_avg = avg

        # On récupère le rang le plus bas qui dépasse la moyenne
        rank = session.query(Rank).filter(Rank.min_points <= avg).order_by(Rank.min_points.desc()).first()
        classroom.rank_id = rank.id if rank else None

    session.add(classroom)

def calculate_delta(user, score):
    score_norm = score / 20.0
    expected = calculate_expected(user)
    delta = 1280 * (score_norm - expected)
    return delta

def update_user_score(session, user, old_score, new_score):
    """
    Met à jour les rank_points de user en retirant l'impact de old_score
    et en appliquant celui de new_score. Met aussi à jour le rang.
    """
    if old_score is not None:
        delta_old = calculate_delta(user, old_score)
        user.rank_points -= delta_old

    delta_new = calculate_delta(user, new_score)
    user.rank_points += delta_new

    update_user_rank(session, user)
    session.add(user)

def remove_user_score(session, user, score):
    if score is None:
        return
    delta = calculate_delta(user, score)
    user.rank_points -= delta
    update_user_rank(session, user)
    session.add(user)

from sqlalchemy import func
from models.homework import Homework
from models.evaluation_note import EvaluationNote

def update_averages(session, user=None, classroom=None):
    """
    Met à jour toutes les moyennes (SubjectFollower, global_average),
    et met à jour rank_points/rank à partir de CHAQUE évaluation et devoir noté.
    """

    users_to_update = [user] if user else session.query(User).all()

    for u in users_to_update:
        # --- Calcul des moyennes par matière ---
        for sf in u.subject_links:
            subject_id = sf.subject_id

            # Moyenne devoirs
            hw_avg = session.query(func.avg(Homework.grade)).filter(
                Homework.user_id == u.id,
                Homework.subject_id == subject_id,
                Homework.grade != None
            ).scalar()

            # Moyenne évaluations pondérées
            eval_data = session.query(
                func.sum(EvaluationNote.score * EvaluationNote.coefficient).label("weighted_sum"),
                func.sum(EvaluationNote.coefficient).label("coeff_sum")
            ).filter(
                EvaluationNote.user_id == u.id,
                EvaluationNote.subject_id == subject_id
            ).one()

            weighted_sum = eval_data.weighted_sum or 0
            coeff_sum = eval_data.coeff_sum or 0
            eval_avg = weighted_sum / coeff_sum if coeff_sum > 0 else None

            # Moyenne combinée
            if hw_avg is not None and eval_avg is not None:
                combined_avg = (hw_avg + eval_avg) / 2
            elif hw_avg is not None:
                combined_avg = hw_avg
            elif eval_avg is not None:
                combined_avg = eval_avg
            else:
                combined_avg = None

            if sf.average != combined_avg:
                sf.average = combined_avg
                session.add(sf)

        # --- Recalcul complet des rank_points à partir de chaque note ---
        u.rank_points = 1000  # Reset de base

        # Devoirs notés
        homeworks = session.query(Homework).filter_by(user_id=u.id).filter(Homework.grade != None).all()
        for hw in homeworks:
            delta = calculate_delta(u, hw.grade)
            u.rank_points += delta

        # Évaluations notées avec coefficient
        evals = session.query(EvaluationNote).filter_by(user_id=u.id).all()
        for e in evals:
            delta = calculate_delta(u, e.score)
            u.rank_points += delta * e.coefficient

        update_user_rank(session, u)
        session.add(u)

        # --- Mise à jour global_average (optionnelle mais utile pour affichage) ---
        averages = [sf.average for sf in u.subject_links if sf.average is not None]
        u.global_average = sum(averages) / len(averages) if averages else None
        session.add(u)

    session.flush()

    # --- Mise à jour des classes ---
    classes_to_update = [classroom] if classroom else session.query(Classroom).all()

    for c in classes_to_update:
        users = c.users
        if not users:
            c.rank_points_avg = None
            c.rank_id = None
            session.add(c)
            continue

        total = 0
        count = 0
        for u in users:
            if u.rank_points is not None:
                total += u.rank_points
                count += 1

        if count > 0:
            avg = total / count
            c.rank_points_avg = avg
        else:
            c.rank_points_avg = None

        update_classroom_rank(session, c)
        session.add(c)

    session.commit()
