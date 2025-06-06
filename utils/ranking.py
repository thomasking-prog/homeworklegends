from models.rank import Rank

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

    session.refresh(user)

def update_rank_points(session, user, new_score):
    score = new_score / 20.0
    expected = calculate_expected(user)
    K = 640

    delta = K * (score - expected)
    user.rank_points += delta

    update_user_rank(session, user)  # 🔁 inclus ici automatiquement

    if user.classroom:
        update_classroom_rank(session, user.classroom)



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
    users = classroom.users  # ou classroom.members selon ta relation
    if not users:
        classroom.rank_points_avg = None
        return

    total = 0
    count = 0
    for user in users:
        if user.rank_points is not None:
            total += user.rank_points
            count += 1

    classroom.rank_points_avg = total / count if count > 0 else None
    session.add(classroom)