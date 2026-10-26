from otree.api import Bot
from . import pages


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield pages.ParticipantID, {'study_participant_id': 'TEST-R-001'}
            yield pages.Instructions

        yield pages.Choice, {
            'choice': 'Heads' if self.round_number % 2 else 'Tails',
        }

        if self.round_number == 150:
            yield pages.FinalPage
