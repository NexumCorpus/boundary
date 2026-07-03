"""Probe family: PARSING VARIANTS (area: parsing-variants).
Legal spellings (case, whitespace, singular/plural, weekday lists) must parse
to the canonical dicts; illegal shapes must raise ValueError.
Each probe returns (name, passed). Trusted code; organisms never see this."""


def _raises_value_error(fn):
    try:
        fn()
    except ValueError:
        return True
    except Exception:
        return False
    return False


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    # -- legal variants; expected dicts derived from brief.md canonical forms.
    # "EVERY 3 DAYS" lower-cases to "every 3 days" -> interval 3.
    check("parsing_upper_every",
          lambda: mod.parse_rule("EVERY 3 DAYS")
          == {"kind": "interval", "days": 3})
    # mixed case; mon=0, thu=3 -> sorted [0, 3].
    check("parsing_mixed_case_weekly",
          lambda: mod.parse_rule("Weekly ON mon,THU")
          == {"kind": "weekly", "weeks": 1, "weekdays": [0, 3]})
    # runs of whitespace collapse; fri=4.
    check("parsing_extra_whitespace",
          lambda: mod.parse_rule("  every   2   weeks   on   fri  ")
          == {"kind": "weekly", "weeks": 2, "weekdays": [4]})
    # singular unit word.
    check("parsing_every_1_day_singular",
          lambda: mod.parse_rule("every 1 day")
          == {"kind": "interval", "days": 1})
    # unit word number-agnostic: "every 1 days" and "every 3 day" both legal.
    check("parsing_singular_plural_swap",
          lambda: mod.parse_rule("every 1 days")
          == {"kind": "interval", "days": 1}
          and mod.parse_rule("every 3 day")
          == {"kind": "interval", "days": 3})
    # optional spaces around weekday names.
    check("parsing_weekday_list_spaces",
          lambda: mod.parse_rule("weekly on mon, thu")
          == {"kind": "weekly", "weeks": 1, "weekdays": [0, 3]})
    # duplicates dropped, output sorted: thu,mon,thu -> [0, 3].
    check("parsing_weekday_dedupe_sort",
          lambda: mod.parse_rule("weekly on thu,mon,thu")
          == {"kind": "weekly", "weeks": 1, "weekdays": [0, 3]})
    # monthly bounds 1 and 30 are both legal.
    check("parsing_monthly_low",
          lambda: mod.parse_rule("monthly on 1")
          == {"kind": "monthly", "day": 1})
    check("parsing_monthly_high",
          lambda: mod.parse_rule("monthly on 30")
          == {"kind": "monthly", "day": 30})

    # -- illegal shapes must raise ValueError (any other outcome = fail).
    check("parsing_invalid_gibberish",
          lambda: _raises_value_error(lambda: mod.parse_rule("sometimes maybe")))
    check("parsing_invalid_zero_interval",
          lambda: _raises_value_error(lambda: mod.parse_rule("every 0 days")))
    check("parsing_invalid_unknown_weekday",
          lambda: _raises_value_error(
              lambda: mod.parse_rule("weekly on funday")))
    check("parsing_invalid_monthly_31",
          lambda: _raises_value_error(lambda: mod.parse_rule("monthly on 31")))
    check("parsing_invalid_monthly_0",
          lambda: _raises_value_error(lambda: mod.parse_rule("monthly on 0")))
    check("parsing_invalid_empty",
          lambda: _raises_value_error(lambda: mod.parse_rule("")))
    check("parsing_invalid_weeks_missing_on",
          lambda: _raises_value_error(lambda: mod.parse_rule("every 2 weeks")))
    check("parsing_invalid_empty_weekday_list",
          lambda: _raises_value_error(lambda: mod.parse_rule("weekly on ")))
    return results
