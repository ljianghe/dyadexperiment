from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)


class Constants(BaseConstants):
    name_in_url = 'otree_dyad_random'
    players_per_group = 2
    num_rounds = 150
    start_tokens = 20


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            for player in self.get_players():
                player.participant.vars['tokens'] = Constants.start_tokens
                player.tokens = Constants.start_tokens


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
    randomizer_used = models.BooleanField(initial=False)
    randomizer_result = models.StringField(blank=True)
    practice1_randomizer_used = models.BooleanField(initial=False)
    practice1_randomizer_result = models.StringField(blank=True)
    practice2_randomizer_used = models.BooleanField(initial=False)
    practice2_randomizer_result = models.StringField(blank=True)
    practice3_randomizer_used = models.BooleanField(initial=False)
    practice3_randomizer_result = models.StringField(blank=True)
