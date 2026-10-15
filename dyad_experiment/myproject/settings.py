from os import environ

SESSION_CONFIGS = [
    dict(
        name='dyad',
        display_name='Dyad two-button',
        num_demo_participants=2,
        app_sequence=['otree_dyad_app'],
    ),
    dict(
        name='otree_dyad_random',
        display_name='Dyad with optional Red/Black randomizer',
        num_demo_participants=2,
        app_sequence=['otree_dyad_random'],
    ),
    dict(
        name='heads_tails_single',
        display_name='Heads and Tails single-player',
        num_demo_participants=1,
        app_sequence=['heads_tails_app'],
    ),
    dict(
        name='heads_tails_random',
        display_name='Heads and Tails with optional randomizer',
        num_demo_participants=1,
        app_sequence=['heads_tails_random'],
    ),
    dict(
        name='red_black_single',
        display_name='Red and Black single-player',
        num_demo_participants=1,
        app_sequence=['red_black_app'],
    ),
    dict(
        name='red_black_random',
        display_name='Red and Black with optional randomizer',
        num_demo_participants=1,
        app_sequence=['red_black_random'],
    ),
]

ROOMS = [
    dict(
        name='room_1',
        display_name='Room 1',
    ),
    dict(
        name='room_2',
        display_name='Room 2',
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '3130331542223'
