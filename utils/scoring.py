# utils/scoring.py
from utils import update_rank_points, update_user_rank, update_user_global_average, update_classroom_rank, calculate_delta

def apply_score_update(session, user, score):
    """
    Applique une note (score sur 20) à un utilisateur :
    - met à jour ses rank_points
    - met à jour son rang
    - met à jour ses moyennes
    - met à jour le classement de sa classe
    """
    update_rank_points(user, score)
    update_user_rank(session, user)
    update_user_global_average(session, user)

    session.add(user)
