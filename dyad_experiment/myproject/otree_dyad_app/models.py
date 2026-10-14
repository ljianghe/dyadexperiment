from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)

import random


class Constants(BaseConstants):
    name_in_url = 'otree_dyad_app'
    players_per_group = 2
    num_rounds = 150
    start_tokens = 20


class Subsession(BaseSubsession):
    def creating_session(self):
        for p in self.get_players():
            if self.round_number == 1:
                p.participant.vars['tokens'] = Constants.start_tokens
                p.tokens = Constants.start_tokens


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    study_participant_id = models.StringField(blank=True, label='Participant ID')
    choice = models.StringField(
        choices=['Red', 'Black', 'NoResponse'],
        widget=widgets.RadioSelectHorizontal,
        blank=True,
    )
    tokens = models.IntegerField()
