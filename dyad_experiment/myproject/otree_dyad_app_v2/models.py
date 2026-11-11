from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)

import random


class Constants(BaseConstants):
    name_in_url = 'dyad_v2'
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
    # Real-trial response tracking. The count is cumulative through this round.
    failed_to_respond = models.BooleanField(initial=False)
    failure_to_respond_count = models.IntegerField(initial=0)
