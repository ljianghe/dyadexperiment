from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)


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
    choice_numeric = models.IntegerField(blank=True)
    predictor_context = models.IntegerField(blank=True)
    predictor_prediction = models.IntegerField(blank=True)
    predictor_miss = models.IntegerField(blank=True)
    cumulative_predictor_misses = models.IntegerField(blank=True)
    r_bonus_cents = models.IntegerField(blank=True)
