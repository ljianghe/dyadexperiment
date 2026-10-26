from otree.api import Page
from otree.common import CSRF_TOKEN_NAME
from .models import Constants
import secrets
from r_condition_scoring import bonus_cents, score_choice


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


class Choice(Page):
    form_model = 'player'
    form_fields = ['choice', 'response_time_ms']

    def vars_for_template(self):
        return {
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
            'csrf_input': _make_csrf_input(self),
        }

    def error_message(self, values):
        if not values.get('choice'):
            return 'Please choose an option to proceed.'

    def before_next_page(self, timeout_happened):
        choice_numeric = 1 if self.choice == 'Heads' else 0
        state, audit = score_choice(
            self.participant.vars.get('r_predictor_state'), choice_numeric
        )
        self.participant.vars['r_predictor_state'] = state
        self.choice_numeric = choice_numeric
        self.predictor_context = audit['context']
        self.predictor_prediction = audit['prediction']
        self.predictor_miss = audit['missed']
        self.cumulative_predictor_misses = audit['misses']

        if self.round_number == Constants.num_rounds:
            payment_cents = bonus_cents(audit['misses'])
            self.r_bonus_cents = payment_cents
            self.participant.vars['r_misses'] = audit['misses']
            self.participant.vars['r_bonus_cents'] = payment_cents


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {
            'csrf_input': _make_csrf_input(self),
        }


class FinalPage(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        payment_cents = self.participant.vars.get('r_bonus_cents', 0)
        balance_key = 'r_condition_balance_recorded'
        if not self.participant.vars.get(balance_key):
            self.participant.vars['total_balance_cents'] = (
                self.participant.vars.get('total_balance_cents', 0)
                + payment_cents
            )
            self.participant.vars[balance_key] = True
        total_balance_cents = self.participant.vars.get('total_balance_cents', 0)
        return {
            'section_earnings': f'{payment_cents / 100:.2f}',
            'total_current_balance': f'{total_balance_cents / 100:.2f}',
        }


page_sequence = [ParticipantID, Instructions, Choice, FinalPage]
