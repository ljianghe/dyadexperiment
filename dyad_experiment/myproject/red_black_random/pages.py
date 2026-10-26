from otree.api import Page
from otree.common import CSRF_TOKEN_NAME
from .models import Constants
from historical_condition_s import (
    find_historical_record,
    save_match_to_participant,
    score_round,
)
import secrets


def _make_csrf_input(page):
    try:
        session = page.request.session
        token = session.get(CSRF_TOKEN_NAME)
        if not token:
            token = secrets.token_hex(16)
            session[CSRF_TOKEN_NAME] = token
        return (
            f'<input type="hidden" '
            f'name="{CSRF_TOKEN_NAME}" '
            f'value="{token}">'
        )
    except Exception:
        return ''


class ParticipantID(Page):
    form_model = 'player'
    form_fields = ['study_participant_id']
    template_name = 'global/ParticipantID.html'

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {'csrf_input': _make_csrf_input(self)}

    def error_message(self, values):
        if not (values.get('study_participant_id') or '').strip():
            return 'Please enter your participant ID.'

    def before_next_page(self, timeout_happened):
        participant_id = self.study_participant_id.strip()
        self.participant.vars['study_participant_id'] = participant_id
        for player in self.in_all_rounds():
            player.study_participant_id = participant_id


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {
            'csrf_input': _make_csrf_input(self),
            'current_player_number': self.participant.vars.get(
                'condition_s_new_role', ''
            )[-1:],
        }


class ComparisonSetup(Page):
    form_model = 'player'
    form_fields = ['comparison_id', 'comparison_entry']

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {'csrf_input': _make_csrf_input(self)}

    def error_message(self, values):
        try:
            find_historical_record(
                values.get('comparison_id', ''), values.get('comparison_entry')
            )
        except (ValueError, RuntimeError) as exc:
            return str(exc)

    def before_next_page(self, timeout_happened):
        record = find_historical_record(
            self.comparison_id, self.field_maybe_none('comparison_entry')
        )
        self.comparison_id = record['participant_id']
        self.comparison_entry = record['entry_number']
        self.historical_player_number = record['historical_role']
        self.current_player_number = record['new_role']
        save_match_to_participant(self.participant, record, Constants.start_tokens)


class Choice(Page):
    form_model = 'player'
    form_fields = [
        'choice', 'randomizer_used', 'randomizer_result', 'response_time_ms'
    ]

    def is_displayed(self):
        return self.participant.vars.get('condition_s_end_round') is None

    def vars_for_template(self):
        return {
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
            'randomizer_outcome': secrets.choice(['Red', 'Black']),
            'csrf_input': _make_csrf_input(self),
        }

    def error_message(self, values):
        if not values.get('choice'):
            return 'Please choose an option to proceed.'

        used = values.get('randomizer_used')
        result = values.get('randomizer_result')
        if used and result not in ['Red', 'Black']:
            return 'The optional randomizer was not recorded correctly. Please try again.'
        if not used and result:
            return 'The optional randomizer was not recorded correctly. Please try again.'

    def before_next_page(self, timeout_happened):
        score_round(self, Constants.start_tokens)


class FinalPage(Page):
    def is_displayed(self):
        return self.participant.vars.get('condition_s_end_round') == self.round_number

    def vars_for_template(self):
        final_tokens = self.participant.vars['condition_s_tokens']
        section_earnings_cents = int(final_tokens) * 10
        balance_key = 'red_black_random_section_balance_recorded'
        if not self.participant.vars.get(balance_key):
            self.participant.vars['total_balance_cents'] = (
                self.participant.vars.get('total_balance_cents', 0)
                + section_earnings_cents
            )
            self.participant.vars[balance_key] = True
        total_balance_cents = self.participant.vars.get('total_balance_cents', 0)
        return {
            'final_tokens': final_tokens,
            'section_earnings': f'{section_earnings_cents / 100:.2f}',
            'total_current_balance': f'{total_balance_cents / 100:.2f}',
            'historical_id': self.participant.vars['condition_s_comparison_id'],
        }


page_sequence = [ParticipantID, ComparisonSetup, Instructions, Choice, FinalPage]
