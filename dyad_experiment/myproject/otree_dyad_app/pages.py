from otree.api import Page, WaitPage
from .models import Constants
from otree.common import CSRF_TOKEN_NAME
import secrets


# ============================================================
# HELPERS
# ============================================================

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


def _apply_payoff(players, no_response_key):
    for p in players:
        p.tokens = p.participant.vars.get(
            'tokens',
            Constants.start_tokens
        )

    p1, p2 = players[0], players[1]

    p1_no_response = p1.participant.vars.get(no_response_key, False)
    p2_no_response = p2.participant.vars.get(no_response_key, False)

    if p1_no_response and p2_no_response:
        p1_payoff = -1
        p2_payoff = -1
    elif p1_no_response:
        p1_payoff = -1
        p2_payoff = 1
    elif p2_no_response:
        p1_payoff = 1
        p2_payoff = -1
    elif p1.choice == p2.choice:
        p1_payoff = 1
        p2_payoff = -1
    else:
        p1_payoff = -1
        p2_payoff = 1

    p1.tokens += p1_payoff
    p2.tokens += p2_payoff

    for p, payoff in zip(players, [p1_payoff, p2_payoff]):
        p.participant.vars['last_round_payoff'] = payoff
        p.participant.vars['tokens'] = p.tokens


def _game_ended(player_or_group, round_number=None):
    players = []
    if hasattr(player_or_group, 'get_players'):
        players = player_or_group.get_players()
    elif isinstance(player_or_group, list):
        players = player_or_group
    else:
        players = [player_or_group]

    reached_limit = (
        round_number is not None and round_number >= Constants.num_rounds
    )

    if reached_limit:
        return True

    for p in players:
        if p.participant.vars.get('tokens', Constants.start_tokens) <= 0:
            return True

    return False


def _live_decision(player, data, attempt_key):
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


# ============================================================
# INSTRUCTIONS
# ============================================================

class Instructions(Page):

    def is_displayed(self):
        # Only show instructions before practice,
        # during oTree round 1.
        return self.round_number == 1


# ============================================================
# PRACTICE CHOICE
# ============================================================

class PracticeChoice(Page):

    form_model = 'player'
    form_fields = ['choice']

    template_name = 'otree_dyad_app/Choice.html'

    # This method builds the variables for the practice page.
    # We explicitly pass the practice round number.
    def practice_vars(self, practice_round_number):

        participant = self.participant

        tokens = participant.vars.get(
            'tokens',
            Constants.start_tokens
        )

        player_choice = self.field_maybe_none('choice')

        return {
            # Actual oTree round
            'round_number': self.round_number,

            # Practice round number
            'practice_round_number': practice_round_number,
            'practice_round_total': 3,

            # Normal round total
            'max_rounds': Constants.num_rounds,

            'tokens': tokens,
            'csrf_input': _make_csrf_input(self),
            'player_choice': player_choice,

            'is_practice': True,
            'practice_round': practice_round_number,
        }

    def is_displayed(self):
        # Practice ONLY happens during oTree round 1.
        return self.round_number == 1

    def error_message(self, values):
        if not values.get('choice'):
            return 'Please choose an option to proceed.'

class PracticeChoice1(PracticeChoice):
    live_method = _practice1_live

    def vars_for_template(self):
        return PracticeChoice.practice_vars(self, 1)

    def before_next_page(self, timeout_happened):
        self.participant.vars['practice1_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


class PracticeChoice2(PracticeChoice):
    live_method = _practice2_live

    def vars_for_template(self):
        return PracticeChoice.practice_vars(self, 2)

    def before_next_page(self, timeout_happened):
        self.participant.vars['practice2_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


class PracticeChoice3(PracticeChoice):
    live_method = _practice3_live

    def vars_for_template(self):
        return PracticeChoice.practice_vars(self, 3)

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


# ============================================================
# PRACTICE WAIT PAGES
# ============================================================

class PracticeBaseWaitPage(WaitPage):

    def is_displayed(self):
        # Practice wait pages only happen in round 1.
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


# ============================================================
# PRACTICE RESULTS
# ============================================================

class PracticeResults(Page):

    template_name = 'otree_dyad_app/Results.html'
    timeout_seconds = 3

    def is_displayed(self):
        # Practice results only happen in oTree round 1.
        return self.round_number == 1

    def practice_vars(self, practice_round_number):

        p = self

        other = None

        p_tokens = Constants.start_tokens
        other_tokens = Constants.start_tokens

        round_payoff = 0
        round_loss = 0

        you_chose = None
        other_chose = None

        if p is not None:

            others = p.get_others_in_group()

            other = others[0] if others else None

            p_tokens = p.participant.vars.get(
                'tokens',
                getattr(
                    p,
                    'tokens',
                    Constants.start_tokens
                )
            )

            if other:
                other_tokens = other.participant.vars.get(
                    'tokens',
                    getattr(
                        other,
                        'tokens',
                        Constants.start_tokens
                    )
                )

            p_choice = p.field_maybe_none('choice')

            other_choice = (
                other.field_maybe_none('choice')
                if other
                else None
            )

            you_chose = p_choice
            other_chose = other_choice

            no_response_key = f'practice{practice_round_number}_no_response'
            player_no_response = p.participant.vars.get(no_response_key, False)
            other_no_response = (
                other.participant.vars.get(no_response_key, False)
                if other
                else False
            )
            round_payoff = p.participant.vars.get('last_round_payoff', 0)

            if round_payoff < 0:
                round_loss = abs(round_payoff)

        return {
            # Actual oTree round
            'round_number': self.round_number,

            # Practice numbering
            'practice_round_number': practice_round_number,
            'practice_round_total': 3,

            # Normal total
            'max_rounds': Constants.num_rounds,

            'p_tokens': p_tokens,
            'other_tokens': other_tokens,

            'you_chose': you_chose,
            'other_chose': other_chose,

            'round_payoff': round_payoff,
            'round_loss': round_loss,
            'player_no_response': player_no_response,
            'other_no_response': other_no_response,

            'is_practice': True,
            'practice_round': practice_round_number,
        }


class PracticeResults1(PracticeResults):

    def vars_for_template(self):
        return PracticeResults.practice_vars(self, 1)


class PracticeResults2(PracticeResults):

    def vars_for_template(self):
        return PracticeResults.practice_vars(self, 2)


class PracticeResults3(PracticeResults):

    def vars_for_template(self):
        return PracticeResults.practice_vars(self, 3)


class RealTrialsIntro(Page):

    def is_displayed(self):
        return self.round_number == 1

    def before_next_page(self, timeout_happened):
        self.tokens = Constants.start_tokens
        self.participant.vars['tokens'] = Constants.start_tokens


class TrialStartWaitPage(WaitPage):

    title_text = 'The next trial will begin shortly.'
    body_text = 'Waiting for both players to be ready.'


# ============================================================
# NORMAL CHOICE
# ============================================================

class Choice(Page):

    form_model = 'player'
    form_fields = ['choice']
    live_method = _real_trial_live

    def vars_for_template(self):

        participant = self.participant

        tokens = participant.vars.get(
            'tokens',
            Constants.start_tokens
        )

        player_choice = self.field_maybe_none('choice')

        return {
            # Real oTree round
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,

            # Explicitly NOT practice
            'practice_round_number': None,
            'practice_round_total': 3,

            'tokens': tokens,
            'csrf_input': _make_csrf_input(self),
            'player_choice': player_choice,

            'is_practice': False,
            'practice_round': None,
        }

    def error_message(self, values):
        if not values.get('choice'):
            return 'Please choose an option to proceed.'

    def before_next_page(self, timeout_happened):
        self.participant.vars[f'round{self.round_number}_no_response'] = (
            self.field_maybe_none('choice') == 'NoResponse'
        )


# ============================================================
# NORMAL RESULTS WAIT PAGE
# ============================================================

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        players = self.group.get_players()
        _apply_payoff(players, f'round{self.round_number}_no_response')


# ============================================================
# NORMAL RESULTS
# ============================================================

class Results(Page):

    timeout_seconds = 3

    def vars_for_template(self):

        p = self

        others = p.get_others_in_group()

        other = others[0] if others else None

        p_tokens = p.participant.vars.get(
            'tokens',
            getattr(
                p,
                'tokens',
                Constants.start_tokens
            )
        )

        other_tokens = (
            other.participant.vars.get(
                'tokens',
                getattr(
                    other,
                    'tokens',
                    Constants.start_tokens
                )
            )
            if other
            else None
        )

        p_choice = p.field_maybe_none('choice')

        other_choice = (
            other.field_maybe_none('choice')
            if other
            else None
        )

        you_chose = p_choice
        other_chose = other_choice

        no_response_key = f'round{self.round_number}_no_response'
        player_no_response = p.participant.vars.get(no_response_key, False)
        other_no_response = (
            other.participant.vars.get(no_response_key, False)
            if other
            else False
        )
        round_payoff = p.participant.vars.get('last_round_payoff', 0)

        round_loss = (
            abs(round_payoff)
            if round_payoff < 0
            else 0
        )

        is_game_over = _game_ended(
            self.group.get_players(),
            self.round_number
        )

        return {
            # Real round
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,

            # Explicitly NOT practice
            'practice_round_number': None,
            'practice_round_total': 3,

            'p_tokens': p_tokens,
            'other_tokens': other_tokens,

            'you_chose': you_chose,
            'other_chose': other_chose,

            'round_payoff': round_payoff,
            'round_loss': round_loss,
            'player_no_response': player_no_response,
            'other_no_response': other_no_response,

            'is_practice': False,
            'practice_round': None,
            'is_game_over': is_game_over,
        }


class FinalPage(Page):

    def is_displayed(self):
        players = self.group.get_players()
        return _game_ended(players, self.round_number)

    def vars_for_template(self):
        p = self
        final_payment = p.participant.vars.get('tokens', getattr(p, 'tokens', 0))

        section_earnings_cents = int(final_payment) * 10
        balance_key = 'dyad_section_balance_recorded'
        if not p.participant.vars.get(balance_key):
            p.participant.vars['total_balance_cents'] = (
                p.participant.vars.get('total_balance_cents', 0)
                + section_earnings_cents
            )
            p.participant.vars[balance_key] = True
        total_balance_cents = p.participant.vars.get('total_balance_cents', 0)

        loser = None
        for player in self.group.get_players():
            if player.participant.vars.get('tokens', getattr(player, 'tokens', 0)) <= 0:
                loser = player.id_in_group
                break

        if loser is None and self.round_number >= Constants.num_rounds:
            loser = None

        return {
            'final_payment': final_payment,
            'final_tokens': final_payment,
            'section_earnings': f'{section_earnings_cents / 100:.2f}',
            'total_current_balance': f'{total_balance_cents / 100:.2f}',
            'player_number': p.id_in_group,
            'loser_number': loser,
            'game_ended_by_tokens': loser is not None,
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
        }


# ============================================================
# PAGE SEQUENCE
# ============================================================

page_sequence = [

    ParticipantID,

    # Instructions: only displayed in round 1
    Instructions,

    # Practice 1: only displayed in round 1
    PracticeStartWaitPage1,
    PracticeChoice1,
    PracticeWaitPage1,
    PracticeResults1,

    # Practice 2: only displayed in round 1
    PracticeStartWaitPage2,
    PracticeChoice2,
    PracticeWaitPage2,
    PracticeResults2,

    # Practice 3: only displayed in round 1
    PracticeStartWaitPage3,
    PracticeChoice3,
    PracticeWaitPage3,
    PracticeResults3,

    # Transition before the real trials begin
    RealTrialsIntro,

    # Real game
    TrialStartWaitPage,
    Choice,
    ResultsWaitPage,
    Results,
    FinalPage,
]
