from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)


class Constants(BaseConstants):
    name_in_url = 'heads_tails_app'
    players_per_group = None
    num_rounds = 150


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
