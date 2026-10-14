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


def _apply_payoff(players):
    for p in players:
        p.tokens = p.participant.vars.get(
            'tokens',
            Constants.start_tokens
        )

    p1, p2 = players[0], players[1]

    p1_choice = p1.choice
    p2_choice = p2.choice

    if p1_choice == p2_choice:
        p1.tokens += 1
        p2.tokens -= 1
    else:
        p1.tokens -= 1
        p2.tokens += 1

    for p in players:
        p.participant.vars['tokens'] = p.tokens


# ============================================================
# INSTRUCTIONS
# ============================================================

class Instructions(Page):

    def is_displayed(self):
        return self.round_number == 1


# ============================================================
# PRACTICE CHOICE
# ============================================================

class PracticeChoice(Page):

    form_model = 'player'
    form_fields = ['choice']

    template_name = 'otree_dyad_app/Choice.html'

    def practice_vars(self, practice_round_number):
        participant = self.participant
        tokens = participant.vars.get('tokens', Constants.start_tokens)
        player_choice = None

        try:
            player_choice = self.choice
        except Exception:
            player_choice = None

        return {
            'round_number': self.round_number,
            'practice_round_number': practice_round_number,
            'practice_round_total': 3,
            'max_rounds': Constants.num_rounds,
            'tokens': tokens,
            'csrf_input': _make_csrf_input(self),
            'player_choice': player_choice,
            'is_practice': True,
            'practice_round': practice_round_number,
        }

    def is_displayed(self):
        return self.round_number == 1

    def error_message(self, values):
        if not values.get('choice'):
            return 'Please choose Red or Black.'


class PracticeChoice1(PracticeChoice):

    def vars_for_template(self):
        return self.practice_vars(1)


class PracticeChoice2(PracticeChoice):

    def vars_for_template(self):
        return self.practice_vars(2)


class PracticeChoice3(PracticeChoice):

    def vars_for_template(self):
        return self.practice_vars(3)


# ============================================================
# PRACTICE WAIT PAGES
# ============================================================

class PracticeBaseWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number == 1

    def after_all_players_arrive(self):
        players = self.group.get_players()
        _apply_payoff(players)


class PracticeWaitPage1(PracticeBaseWaitPage):
    pass


class PracticeWaitPage2(PracticeBaseWaitPage):
    pass


class PracticeWaitPage3(PracticeBaseWaitPage):
    pass


# ============================================================
# PRACTICE RESULTS
# ============================================================

class PracticeResults(Page):

    template_name = 'otree_dyad_app/Results.html'

    def is_displayed(self):
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
                getattr(p, 'tokens', Constants.start_tokens)
            )

            if other:
                other_tokens = other.participant.vars.get(
                    'tokens',
                    getattr(other, 'tokens', Constants.start_tokens)
                )

            p_choice = getattr(p, 'choice', None)
            other_choice = getattr(other, 'choice', None) if other else None
            you_chose = p_choice
            other_chose = other_choice

            if p_choice is not None and other_choice is not None:
                if p.id_in_group == 1:
                    round_payoff = 1 if p_choice == other_choice else -1
                else:
                    round_payoff = -1 if p_choice == other_choice else 1

            if round_payoff < 0:
                round_loss = abs(round_payoff)

        return {
            'round_number': self.round_number,
            'practice_round_number': practice_round_number,
            'practice_round_total': 3,
            'max_rounds': Constants.num_rounds,
            'p_tokens': p_tokens,
            'other_tokens': other_tokens,
            'you_chose': you_chose,
            'other_chose': other_chose,
            'round_payoff': round_payoff,
            'round_loss': round_loss,
            'is_practice': True,
            'practice_round': practice_round_number,
        }


class PracticeResults1(PracticeResults):

    def vars_for_template(self):
        return self.practice_vars(1)


class PracticeResults2(PracticeResults):

    def vars_for_template(self):
        return self.practice_vars(2)


class PracticeResults3(PracticeResults):

    def vars_for_template(self):
        return self.practice_vars(3)


# ============================================================
# NORMAL CHOICE
# ============================================================

class Choice(Page):

    form_model = 'player'
    form_fields = ['choice']

    def vars_for_template(self):
        participant = self.participant
        tokens = participant.vars.get('tokens', Constants.start_tokens)
        player_choice = getattr(self, 'choice', None)

        return {
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
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
            return 'Please choose Red or Black.'


# ============================================================
# NORMAL RESULTS WAIT PAGE
# ============================================================

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        players = self.group.get_players()
        _apply_payoff(players)


# ============================================================
# NORMAL RESULTS
# ============================================================

class Results(Page):

    def vars_for_template(self):
        p = self
        others = p.get_others_in_group()
        other = others[0] if others else None

        p_tokens = p.participant.vars.get(
            'tokens',
            getattr(p, 'tokens', Constants.start_tokens)
        )

        other_tokens = (
            other.participant.vars.get(
                'tokens',
                getattr(other, 'tokens', Constants.start_tokens)
            )
            if other else None
        )

        p_choice = getattr(p, 'choice', None)
        other_choice = getattr(other, 'choice', None) if other else None
        you_chose = p_choice
        other_chose = other_choice

        round_payoff = 0

        if p_choice is not None and other_choice is not None:
            if p.id_in_group == 1:
                round_payoff = 1 if p_choice == other_choice else -1
            else:
                round_payoff = -1 if p_choice == other_choice else 1

        round_loss = abs(round_payoff) if round_payoff < 0 else 0

        return {
            'round_number': self.round_number,
            'max_rounds': Constants.num_rounds,
            'practice_round_number': None,
            'practice_round_total': 3,
            'p_tokens': p_tokens,
            'other_tokens': other_tokens,
            'you_chose': you_chose,
            'other_chose': other_chose,
            'round_payoff': round_payoff,
            'round_loss': round_loss,
            'is_practice': False,
            'practice_round': None,
        }


# ============================================================
# PAGE SEQUENCE
# ============================================================

page_sequence = [
    Instructions,
    PracticeChoice1,
    PracticeWaitPage1,
    PracticeResults1,
    PracticeChoice2,
    PracticeWaitPage2,
    PracticeResults2,
    PracticeChoice3,
    PracticeWaitPage3,
    PracticeResults3,
    Choice,
    ResultsWaitPage,
    Results,
]
