"""Recurrence expander. See brief.md for the rule grammar, the day model
(day 0 = Monday, 30-day months) and the exact semantics of each function."""


def parse_rule(text):
    raise NotImplementedError


def occurrences(rule_dict, start_day, end_day):
    raise NotImplementedError


def next_after(rule_dict, day):
    raise NotImplementedError


def count_in(rule_dict, start_day, end_day):
    raise NotImplementedError
