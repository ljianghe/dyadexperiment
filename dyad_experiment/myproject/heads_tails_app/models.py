from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from r_condition_scoring import bonus_cents, score_choice


class Constants(BaseConstants):
    name_in_url = 'heads_tails_app'
    players_per_group = None
    num_rounds = 150
    bonus_threshold_misses = 60
    bonus_cents_per_miss = 12


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    study_participant_id = models.StringField(blank=True, label='Participant ID')
    response_time_ms = models.IntegerField(blank=True)
    choice = models.StringField(
        choices=['Heads', 'Tails'],
        widget=widgets.RadioSelectHorizontal,
        blank=True,
    )


def custom_export_scored(players):
    """Reconstruct predictor scores from saved choices without extra DB columns."""
    yield [
        'session_code', 'participant_code', 'study_participant_id',
        'round_number', 'choice', 'response_time_ms', 'choice_numeric',
        'predictor_context', 'predictor_prediction', 'predictor_miss',
        'cumulative_predictor_misses', 'r_bonus_cents',
    ]
    states = {}
    ordered_players = sorted(
        players, key=lambda p: (p.session_id, p.participant_id, p.round_number)
    )
    for player in ordered_players:
        key = (player.session_id, player.participant_id)
        if player.choice not in ('Heads', 'Tails'):
            yield [
                player.session.code, player.participant.code,
                player.study_participant_id, player.round_number,
                player.choice, player.response_time_ms,
                '', '', '', '', '', '',
            ]
            continue
        choice_numeric = 1 if player.choice == 'Heads' else 0
        state, audit = score_choice(states.get(key), choice_numeric)
        states[key] = state
        payment_cents = (
            bonus_cents(audit['misses'])
            if player.round_number == Constants.num_rounds else ''
        )
        yield [
            player.session.code, player.participant.code,
            player.study_participant_id, player.round_number,
            player.choice, player.response_time_ms, choice_numeric,
            audit['context'], audit['prediction'], audit['missed'],
            audit['misses'], payment_cents,
        ]
