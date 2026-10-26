"""Scoring for the 150-round Heads/Tails (R) condition."""


def initial_predictor_state():
    return {
        'p1': -1,
        'p2': -1,
        'misses': 0,
        'H0': 0,
        'T0': 0,
        'H1': 0,
        'T1': 0,
        'H2': 0,
        'T2': 0,
        'H3': 0,
        'T3': 0,
    }


def score_choice(previous_state, choice):
    """Score one binary choice and return the new state and audit values."""
    if choice not in (0, 1):
        raise ValueError('R-condition choice must be 0 (Tails) or 1 (Heads).')

    state = dict(previous_state or initial_predictor_state())
    context = 2 * state['p2'] + state['p1'] if state['p2'] >= 0 else -1

    if context >= 0:
        heads_count = state[f'H{context}']
        tails_count = state[f'T{context}']
    else:
        heads_count = tails_count = 0

    prediction = 1 if heads_count >= tails_count else 0
    missed = int(choice != prediction)
    state['misses'] += missed

    if context >= 0:
        if choice == 1:
            state[f'H{context}'] += 1
        else:
            state[f'T{context}'] += 1

    state['p2'] = state['p1']
    state['p1'] = choice

    return state, {
        'context': context,
        'prediction': prediction,
        'missed': missed,
        'misses': state['misses'],
    }


def bonus_cents(misses):
    """Pay 12 cents for every predictor miss above 60."""
    return 12 * max(0, int(misses) - 60)
