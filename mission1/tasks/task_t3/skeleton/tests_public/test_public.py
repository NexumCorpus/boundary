import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recur import count_in, next_after, occurrences, parse_rule


def test_parse_every_days():
    assert parse_rule("every 3 days") == {"kind": "interval", "days": 3}


def test_parse_weekly_list():
    assert parse_rule("weekly on mon,thu") == {
        "kind": "weekly", "weeks": 1, "weekdays": [0, 3]}


def test_occurrences_interval():
    assert occurrences(parse_rule("every 3 days"), 0, 10) == [0, 3, 6, 9]


def test_occurrences_weekly():
    assert occurrences(parse_rule("weekly on mon"), 0, 20) == [0, 7, 14]


def test_next_after_monthly():
    assert next_after(parse_rule("monthly on 15"), 0) == 14


def test_count_in_biweekly():
    assert count_in(parse_rule("every 2 weeks on fri"), 0, 27) == 2
