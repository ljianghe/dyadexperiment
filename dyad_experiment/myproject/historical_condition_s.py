"""Read and score the historical Condition S response workbook."""

from functools import lru_cache
from pathlib import Path
import re
from xml.etree import ElementTree
from zipfile import ZipFile

WORKBOOK_PATH = Path(__file__).with_name('allformerconditionS.xlsx')
CHOICE_MAP = {'A': 'Red', 'B': 'Black'}
XML_NAMESPACE = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def _column_index(cell_reference):
    letters = re.match(r'[A-Z]+', cell_reference).group(0)
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter) - ord('A') + 1
    return index - 1


def _read_first_sheet_rows(path):
    """Read the simple values needed here without a deployment dependency."""
    with ZipFile(path) as archive:
        shared_root = ElementTree.fromstring(archive.read('xl/sharedStrings.xml'))
        shared_strings = [
            ''.join(node.text or '' for node in item.findall('.//x:t', XML_NAMESPACE))
            for item in shared_root.findall('x:si', XML_NAMESPACE)
        ]
        sheet_root = ElementTree.fromstring(archive.read('xl/worksheets/sheet1.xml'))

    for row_node in sheet_root.findall('.//x:sheetData/x:row', XML_NAMESPACE):
        values = [None] * 152
        for cell in row_node.findall('x:c', XML_NAMESPACE):
            reference = cell.attrib.get('r', '')
            column = _column_index(reference)
            if column >= len(values):
                continue
            value_node = cell.find('x:v', XML_NAMESPACE)
            if value_node is None:
                continue
            value = value_node.text
            if cell.attrib.get('t') == 's':
                value = shared_strings[int(value)]
            values[column] = value
        yield tuple(values)


def normalize_participant_id(value):
    """Make Excel numeric IDs and typed text IDs comparable."""
    text = str(value).strip()
    if text.endswith('.0'):
        try:
            number = float(text)
            if number.is_integer():
                return str(int(number))
        except ValueError:
            pass
    return text


@lru_cache(maxsize=1)
def historical_records():
    if not WORKBOOK_PATH.exists():
        raise RuntimeError(f'Historical response file not found: {WORKBOOK_PATH.name}')

    rows = _read_first_sheet_rows(WORKBOOK_PATH)
    headers = next(rows, None)
    expected = ('Student ID', 'Player #')
    if not headers or tuple(headers[:2]) != expected:
        raise RuntimeError('The historical workbook has unexpected column headings.')

    by_id = {}
    for row in rows:
        if not row or row[0] in (None, ''):
            continue

        participant_id = normalize_participant_id(row[0])
        role = str(row[1]).strip().upper()
        if role not in ('P1', 'P2'):
            raise RuntimeError(f'Invalid player number for historical ID {participant_id}.')

        raw_choices = tuple(row[2:152])
        if len(raw_choices) != 150:
            raise RuntimeError(f'Historical ID {participant_id} does not have 150 choices.')
        try:
            choices = tuple(CHOICE_MAP[str(value).strip().upper()] for value in raw_choices)
        except KeyError as exc:
            raise RuntimeError(
                f'Historical ID {participant_id} contains a choice other than A or B.'
            ) from exc

        records = by_id.setdefault(participant_id, [])
        records.append(
            {
                'participant_id': participant_id,
                'entry_number': len(records) + 1,
                'historical_role': role,
                'new_role': 'P2' if role == 'P1' else 'P1',
                'choices': choices,
            }
        )

    if not by_id:
        raise RuntimeError('The historical workbook contains no participant records.')
    return by_id


def find_historical_record(participant_id, entry_number=None):
    normalized_id = normalize_participant_id(participant_id)
    records = historical_records().get(normalized_id)
    if not records:
        raise ValueError(f'Participant ID {normalized_id or "(blank)"} was not found.')

    if len(records) > 1 and entry_number in (None, ''):
        raise ValueError(
            f'Participant ID {normalized_id} has {len(records)} entries. '
            f'Enter an entry number from 1 to {len(records)}.'
        )

    selected_entry = 1 if entry_number in (None, '') else int(entry_number)
    if selected_entry < 1 or selected_entry > len(records):
        raise ValueError(
            f'Participant ID {normalized_id} has entry numbers 1 through {len(records)}.'
        )
    return records[selected_entry - 1]


def save_match_to_participant(participant, record, start_tokens=20):
    participant.vars['condition_s_comparison_id'] = record['participant_id']
    participant.vars['condition_s_comparison_entry'] = record['entry_number']
    participant.vars['condition_s_historical_role'] = record['historical_role']
    participant.vars['condition_s_new_role'] = record['new_role']
    participant.vars['condition_s_historical_choices'] = record['choices']
    participant.vars['condition_s_tokens'] = start_tokens
    participant.vars['condition_s_historical_tokens'] = start_tokens
    participant.vars['condition_s_end_round'] = None


def score_round(player, start_tokens=20):
    participant = player.participant
    choices = participant.vars['condition_s_historical_choices']
    historical_choice = choices[player.round_number - 1]
    new_role = participant.vars['condition_s_new_role']
    is_match = player.choice == historical_choice

    if new_role == 'P1':
        payoff = 1 if is_match else -1
    else:
        payoff = -1 if is_match else 1

    tokens = participant.vars.get('condition_s_tokens', start_tokens) + payoff
    historical_tokens = (
        participant.vars.get('condition_s_historical_tokens', start_tokens) - payoff
    )

    player.historical_choice = historical_choice
    player.round_payoff = payoff
    player.tokens = tokens
    player.historical_tokens = historical_tokens
    participant.vars['condition_s_tokens'] = tokens
    participant.vars['condition_s_historical_tokens'] = historical_tokens

    if tokens <= 0 or historical_tokens <= 0 or player.round_number == 150:
        participant.vars['condition_s_end_round'] = player.round_number
