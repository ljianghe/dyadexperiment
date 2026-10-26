from otree.api import Bot
from . import pages


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield pages.ParticipantID, {'study_participant_id': 'TEST-R-001'}
            yield pages.Instructions

        if self.round_number % 2:
            yield pages.Choice, {
                'choice': 'Heads',
                'randomizer_used': True,
                'randomizer_result': 'Heads',
            }
        else:
            yield pages.Choice, {
                'choice': 'Tails',
                'randomizer_used': False,
                'randomizer_result': '',
            }

        if self.round_number == 150:
            yield pages.FinalPage
