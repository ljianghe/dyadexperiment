from otree.api import Bot

from historical_condition_s import find_historical_record
from . import pages


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield pages.ParticipantID, {'study_participant_id': 'TEST-S-001'}
            yield pages.ComparisonSetup, {
                'comparison_id': '162000',
                'comparison_entry': '',
            }
            yield pages.Instructions

        if self.participant.vars.get('condition_s_end_round') is None:
            historical_choice = find_historical_record('162000')['choices'][
                self.round_number - 1
            ]
            yield pages.Choice, {'choice': historical_choice}

        if self.participant.vars.get('condition_s_end_round') == self.round_number:
            yield pages.FinalPage
