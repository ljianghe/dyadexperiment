from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)


class Constants(BaseConstants):
    name_in_url = 'red_black_app'
    players_per_group = None
    num_rounds = 150
    start_tokens = 20


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    study_participant_id = models.StringField(blank=True, label='Participant ID')
    response_time_ms = models.IntegerField(blank=True)
    comparison_id = models.StringField(blank=True, label='Historical participant ID')
    comparison_entry = models.IntegerField(
        blank=True,
        min=1,
        label='Entry number (only needed when an ID appears more than once)',
    )
    historical_player_number = models.StringField(blank=True)
    current_player_number = models.StringField(blank=True)
    choice = models.StringField(
        choices=['Red', 'Black'],
        widget=widgets.RadioSelectHorizontal,
        blank=True,
    )
    historical_choice = models.StringField(blank=True)
    round_payoff = models.IntegerField(blank=True)
    tokens = models.IntegerField(blank=True)
    historical_tokens = models.IntegerField(blank=True)
