# Task T3: recurrence expander

Implement `recur.py` in this directory. It expands textual recurrence rules
("every 3 days", "weekly on mon,thu", ...) into concrete day numbers.

## Day model

- Days are integers. **Day 0 is a Monday.** Weekday of day `d` is `d % 7`,
  with `0=mon, 1=tue, 2=wed, 3=thu, 4=fri, 5=sat, 6=sun`.
- Week number of day `d` is `d // 7` (week 0 = days 0..6).
- Months are fixed **30-day months**: "monthly on N" (1 <= N <= 30) hits every
  day `d` with `d % 30 == N - 1` (so "monthly on 1" hits days 0, 30, 60, ...).
- Occurrences exist only on days `d >= 0`. Negative days never contain
  occurrences (a window that dips below 0 is effectively clipped at 0).

## Required functions

### `parse_rule(text) -> dict`

Parse a rule string. Matching is **case-insensitive**; leading/trailing
whitespace and runs of internal whitespace are ignored (i.e. normalize by
lowercasing and collapsing whitespace before matching). The accepted shapes,
and the EXACT canonical dict returned for each:

1. `every N day` / `every N days` — N is one or more ASCII digits (base-10),
   N >= 1. The unit word may be singular or plural regardless of N
   ("every 1 days" and "every 3 day" are both valid).
   Returns `{"kind": "interval", "days": N}`.
2. `weekly on <weekdays>` — equivalent to "every 1 weeks on <weekdays>".
   Returns `{"kind": "weekly", "weeks": 1, "weekdays": [...]}`.
3. `every N week[s] on <weekdays>` — N >= 1, singular/plural as above.
   Returns `{"kind": "weekly", "weeks": N, "weekdays": [...]}`.
4. `monthly on N` — 1 <= N <= 30.
   Returns `{"kind": "monthly", "day": N}`.

`<weekdays>` is a comma-separated list of the three-letter names
`mon,tue,wed,thu,fri,sat,sun` (case-insensitive; optional whitespace around
each name). At least one name is required. Duplicates are allowed and
deduplicated. The canonical `"weekdays"` value is the **sorted list of unique
weekday integers** (e.g. "thu,mon,thu" -> `[0, 3]`).

Anything else raises **ValueError**: unknown shapes ("sometimes", ""),
`every 0 days`, weeks-form without `on <weekdays>` ("every 2 weeks"),
unknown weekday names ("weekly on funday"), empty weekday list,
`monthly on 0`, `monthly on 31`, non-integer counts.

### `occurrences(rule_dict, start_day: int, end_day: int) -> list[int]`

All occurrence days `d` with `start_day <= d <= end_day` (**inclusive** on
both ends), sorted ascending. If `start_day > end_day`, return `[]`.
Occurrence membership, anchored at day 0:

- interval: `d % days == 0` (days 0, N, 2N, ...).
- weekly: `d % 7` is in `weekdays` **and** `(d // 7) % weeks == 0`
  (i.e. "every 2 weeks on fri" hits Fridays of weeks 0, 2, 4, ...).
- monthly: `d % 30 == day - 1`.
- In every case, additionally `d >= 0`.

### `next_after(rule_dict, day: int) -> int`

The smallest occurrence day **strictly greater** than `day`. Scan no further
than `day + 10000` (inclusive); if no occurrence exists in
`day+1 .. day+10000`, raise **ValueError**.

### `count_in(rule_dict, start_day, end_day) -> int`

Exactly `len(occurrences(rule_dict, start_day, end_day))`.

## Running the public tests

    python -m pytest tests_public/ -q

## Correctness areas

- `parsing-variants` — parse_rule accepts all legal spellings (case,
  whitespace, singular/plural, weekday lists) and raises ValueError on every
  illegal shape.
- `window-boundaries` — inclusive window edges, empty/inverted windows, and
  next_after strictness/ValueError behavior are exact.
- `weekday-mapping` — weekly rules land only on the declared weekdays under
  the day-0-is-Monday mapping, including every-N-weeks week filtering.
- `monthly-arithmetic` — 30-day-month day numbers (`d % 30 == N - 1`) are
  correct across months and unaligned windows.
- `cross-function-consistency` — count_in, occurrences, and next_after agree
  with each other, output is sorted strictly increasing, and calls are
  deterministic.
