from otree.api import Page, WaitPage
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
        return f'<input type="hidden" name="{CSRF_TOKEN_NAME}" value="{token}">'
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


def _apply_payoff(players, no_response_key):
    for player in players:
        player.tokens = player.participant.vars.get('tokens', Constants.start_tokens)

    player1, player2 = players
    player1_no_response = player1.participant.vars.get(no_response_key, False)
    player2_no_response = player2.participant.vars.get(no_response_key, False)

    if player1_no_response and player2_no_response:
        player1_payoff = -1
        player2_payoff = -1
    elif player1_no_response:
        player1_payoff = -1
        player2_payoff = 1
    elif player2_no_response:
        player1_payoff = 1
        player2_payoff = -1
    elif player1.choice == player2.choice:
        player1_payoff = 1
        player2_payoff = -1
    else:
        player1_payoff = -1
        player2_payoff = 1

    player1.tokens += player1_payoff
    player2.tokens += player2_payoff

    for player, payoff in zip(players, [player1_payoff, player2_payoff]):
        player.participant.vars['last_round_payoff'] = payoff
        player.participant.vars['tokens'] = player.tokens


def _game_ended(players, round_number):
    if round_number >= Constants.num_rounds:
        return True
    return any(
        player.participant.vars.get('tokens', Constants.start_tokens) <= 0
        for player in players
    )


def _choice_and_randomizer_error(values, used_field, result_field):
    if not values.get('choice'):
        return 'Please choose an option to proceed.'

    used = values.get(used_field)
    result = values.get(result_field)
    if used and result not in ['Red', 'Black']:
        return 'The optional Red/Black coin was not recorded correctly. Please try again.'
    if not used and result:
        return 'The optional Red/Black coin was not recorded correctly. Please try again.'


def _randomizer_field_names(attempt_key):
    if attempt_key in ['practice1', 'practice2', 'practice3']:
        return (
            f'{attempt_key}_randomizer_used',
            f'{attempt_key}_randomizer_result',
        )
    return 'randomizer_used', 'randomizer_result'


def _randomizer_retry_vars(player, attempt_key):
    used_field, result_field = _randomizer_field_names(attempt_key)
    saved_result = player.field_maybe_none(result_field)
    already_used = (
        bool(player.field_maybe_none(used_field))
        and saved_result in ['Red', 'Black']
    )
    return {
        'randomizer_outcome': (
            saved_result if already_used else secrets.choice(['Red', 'Black'])
        ),
        'randomizer_already_used': already_used,
        'persisted_randomizer_result': saved_result if already_used else '',
        'randomizer_used_value': 'True' if already_used else 'False',
        'randomizer_storage_key': (
            f'dyad-randomizer:{player.session.code}:'
            f'{player.participant.code}:{attempt_key}'
        ),
    }


def _live_decision(player, data, attempt_key):
    if isinstance(data, dict):
        randomizer_result = data.get('randomizer_result')
        if randomizer_result in ['Red', 'Black']:
            used_field, result_field = _randomizer_field_names(attempt_key)
            saved_result = player.field_maybe_none(result_field)
            if saved_result not in ['Red', 'Black']:
                setattr(player, used_field, True)
                setattr(player, result_field, randomizer_result)

        if data.get('type') == 'randomizer':
            _, result_field = _randomizer_field_names(attempt_key)
            return {
                player.id_in_group: {
                    'randomizer_saved': True,
                    'randomizer_result': player.field_maybe_none(result_field),
                }
            }

    choice = data.get('choice') if isinstance(data, dict) else None
    if choice not in ['Red', 'Black']:
        choice = None

    arrived_key = f'{attempt_key}_live_arrived'
    choice_key = f'{attempt_key}_live_choice'
    player.participant.vars[arrived_key] = True
    player.participant.vars[choice_key] = choice

    players = player.group.get_players()
    if not all(p.participant.vars.get(arrived_key, False) for p in players):
        return

    retry = any(p.participant.vars.get(choice_key) is None for p in players)
    for group_player in players:
        group_player.participant.vars.pop(arrived_key, None)
        group_player.participant.vars.pop(choice_key, None)

    return {0: {'retry': retry, 'success': not retry}}


def _practice1_live(player, data):
    return _live_decision(player, data, 'practice1')


def _practice2_live(player, data):
    return _live_decision(player, data, 'practice2')


def _practice3_live(player, data):
    return _live_decision(player, data, 'practice3')


def _real_trial_live(player, data):
    return _live_decision(player, data, f'round{player.round_number}')


def _results_vars(page, is_practice=False, practice_round_number=None):
    player = page
    others = player.get_others_in_group()
    other = others[0] if others else None
    player_tokens = player.participant.vars.get('tokens', player.tokens)
    other_tokens = (
        other.participant.vars.get('tokens', other.tokens) if other else None
    )
    player_choice = player.field_maybe_none('choice')
    other_choice = other.field_maybe_none('choice') if other else None
    no_response_key = (
        f'practice{practice_round_number}_no_response'
        if is_practice
        else f'round{page.round_number}_no_response'
    )
    player_no_response = player.participant.vars.get(no_response_key, False)
    other_no_response = (
        other.participant.vars.get(no_response_key, False) if other else False
    )
    payoff = player.participant.vars.get('last_round_payoff', 0)

    return {
        'round_number': page.round_number,
        'max_rounds': Constants.num_rounds,
        'practice_round_number': practice_round_number,
        'practice_round_total': 3,
        'p_tokens': player_tokens,
        'other_tokens': other_tokens,
        'you_chose': player_choice,
        'other_chose': other_choice,
        'round_payoff': payoff,
        'round_loss': abs(payoff) if payoff < 0 else 0,
        'player_no_response': player_no_response,
        'other_no_response': other_no_response,
        'is_practice': is_practice,
        'practice_round': practice_round_number,
        'is_game_over': _game_ended(page.group.get_players(), page.round_number),
    }


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1


class GameInstructions(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {'player_number': self.id_in_group}


class RandomizerInstructions(Page):
    def is_displayed(self):
        return self.round_number == 1


class PracticeInstructions(Page):
    def is_displayed(self):
        return self.round_number == 1


class PracticeChoice(Page):
    form_model = 'player'
    form_fields = ['choice']
    template_name = 'otree_dyad_random/Choice.html'

    def is_displayed(self):
        return self.round_number == 1

    def practice_vars(self, practice_round_number):
        attempt_key = f'practice{practice_round_number}'
        return {
            'round_number': self.round_number,
            'practice_round_number': practice_round_number,
            'practice_round_total': 3,
            'max_rounds': Constants.num_rounds,
            'tokens': self.participant.vars.get('tokens', Constants.start_tokens),
            'csrf_input': _make_csrf_input(self),
            'is_practice': True,
            'practice_round': practice_round_number,
            **_randomizer_retry_vars(self, attempt_key),
            'randomizer_used_field': f'practice{practice_round_number}_randomizer_used',
            'randomizer_result_field': f'practice{practice_round_number}_randomizer_result',
        }

class PracticeChoice1(PracticeChoice):
    live_method = _practice1_live
    form_fields = ['choice', 'practice1_randomizer_used', 'practice1_randomizer_result']

    def vars_for_template(self):
        return PracticeChoice.practice_vars(self, 1)

    def error_message(self, values):
        return _choice_and_randomizer_error(
            values, 'practice1_randomizer_used', 'practice1_randomizer_result'
        )

    def before_next_page(self, timeout_happened):
        self.participant.vars['practice1_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


class PracticeChoice2(PracticeChoice):
    live_method = _practice2_live
    form_fields = ['choice', 'practice2_randomizer_used', 'practice2_randomizer_result']

    def vars_for_template(self):
        return PracticeChoice.practice_vars(self, 2)

    def error_message(self, values):
        return _choice_and_randomizer_error(
            values, 'practice2_randomizer_used', 'practice2_randomizer_result'
        )

    def before_next_page(self, timeout_happened):
        self.participant.vars['practice2_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


class PracticeChoice3(PracticeChoice):
    live_method = _practice3_live
    form_fields = ['choice', 'practice3_randomizer_used', 'practice3_randomizer_result']

    def vars_for_template(self):
        return PracticeChoice.practice_vars(self, 3)

    def error_message(self, values):
        return _choice_and_randomizer_error(
            values, 'practice3_randomizer_used', 'practice3_randomizer_result'
        )

    def before_next_page(self, timeout_happened):
        self.participant.vars['practice3_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


class PracticeStartWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number == 1

    title_text = 'The next trial will begin shortly.'
    body_text = 'Waiting for both players to be ready.'


class PracticeStartWaitPage1(PracticeStartWaitPage):
    pass


class PracticeStartWaitPage2(PracticeStartWaitPage):
    pass


class PracticeStartWaitPage3(PracticeStartWaitPage):
    pass


class PracticeBaseWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number == 1

class PracticeWaitPage1(PracticeBaseWaitPage):
    def after_all_players_arrive(self):
        _apply_payoff(self.group.get_players(), 'practice1_no_response')


class PracticeWaitPage2(PracticeBaseWaitPage):
    def after_all_players_arrive(self):
        _apply_payoff(self.group.get_players(), 'practice2_no_response')


class PracticeWaitPage3(PracticeBaseWaitPage):
    def after_all_players_arrive(self):
        _apply_payoff(self.group.get_players(), 'practice3_no_response')


class PracticeResults(Page):
    template_name = 'otree_dyad_random/Results.html'
    timeout_seconds = 3

    def is_displayed(self):
        return self.round_number == 1

class PracticeResults1(PracticeResults):
    def vars_for_template(self):
        return _results_vars(self, True, 1)


class PracticeResults2(PracticeResults):
    def vars_for_template(self):
        return _results_vars(self, True, 2)


class PracticeResults3(PracticeResults):
    def vars_for_template(self):
        return _results_vars(self, True, 3)


class RealTrialsIntro(Page):
    def is_displayed(self):
        return self.round_number == 1

    def before_next_page(self, timeout_happened):
        self.tokens = Constants.start_tokens
        self.participant.vars['tokens'] = Constants.start_tokens


class TrialStartWaitPage(WaitPage):
    title_text = 'The next trial will begin shortly.'
    body_text = 'Waiting for both players to be ready.'


class Choice(Page):
    form_model = 'player'
    form_fields = ['choice', 'randomizer_used', 'randomizer_result']
    live_method = _real_trial_live

    def vars_for_template(self):
        attempt_key = f'round{self.round_number}'
        return {
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
            'tokens': self.participant.vars.get('tokens', Constants.start_tokens),
            'csrf_input': _make_csrf_input(self),
            'is_practice': False,
            'practice_round': None,
            **_randomizer_retry_vars(self, attempt_key),
            'randomizer_used_field': 'randomizer_used',
            'randomizer_result_field': 'randomizer_result',
        }

    def error_message(self, values):
        return _choice_and_randomizer_error(
            values, 'randomizer_used', 'randomizer_result'
        )

    def before_next_page(self, timeout_happened):
        self.participant.vars[f'round{self.round_number}_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        _apply_payoff(
            self.group.get_players(),
            f'round{self.round_number}_no_response',
        )


class Results(Page):
    timeout_seconds = 3

    def vars_for_template(self):
        return _results_vars(self)


class FinalPage(Page):
    def is_displayed(self):
        return _game_ended(self.group.get_players(), self.round_number)

    def vars_for_template(self):
        player = self
        final_tokens = player.participant.vars.get('tokens', player.tokens)
        section_earnings_cents = int(final_tokens) * 10
        balance_key = 'dyad_random_section_balance_recorded'
        if not player.participant.vars.get(balance_key):
            player.participant.vars['total_balance_cents'] = (
                player.participant.vars.get('total_balance_cents', 0)
                + section_earnings_cents
            )
            player.participant.vars[balance_key] = True
        total_balance_cents = player.participant.vars.get('total_balance_cents', 0)
        loser = next((
            p.id_in_group for p in self.group.get_players()
            if p.participant.vars.get('tokens', p.tokens) <= 0
        ), None)
        return {
            'final_payment': final_tokens,
            'final_tokens': final_tokens,
            'section_earnings': f'{section_earnings_cents / 100:.2f}',
            'total_current_balance': f'{total_balance_cents / 100:.2f}',
            'player_number': player.id_in_group,
            'loser_number': loser,
            'game_ended_by_tokens': loser is not None,
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
        }


page_sequence = [
    ParticipantID,
    Instructions,
    GameInstructions,
    RandomizerInstructions,
    PracticeInstructions,
    PracticeStartWaitPage1, PracticeChoice1, PracticeWaitPage1, PracticeResults1,
    PracticeStartWaitPage2, PracticeChoice2, PracticeWaitPage2, PracticeResults2,
    PracticeStartWaitPage3, PracticeChoice3, PracticeWaitPage3, PracticeResults3,
    RealTrialsIntro,
    TrialStartWaitPage, Choice, ResultsWaitPage, Results, FinalPage,
]
