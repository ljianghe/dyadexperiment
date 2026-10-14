from otree.api import Page
from otree.common import CSRF_TOKEN_NAME
from .models import Constants
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


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {
            'csrf_input': _make_csrf_input(self),
        }


page_sequence = [ParticipantID, Instructions, Choice]
