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

def calculate_delta(user, score):
    score_norm = score / 20.0
    expected = calculate_expected(user)
    delta = 640 * (score_norm - expected)
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
