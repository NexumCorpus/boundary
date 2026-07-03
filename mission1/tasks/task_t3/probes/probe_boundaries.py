"""Probe family: WINDOW BOUNDARIES (area: window-boundaries).
Inclusive edges, empty/inverted windows, next_after strictness and its
no-occurrence-within-10000-days ValueError.
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

    # "every 3 days" hits d % 3 == 0: days 0, 3, 6, 9, 12, ...
    r3 = lambda: mod.parse_rule("every 3 days")

    # window [6, 6]: 6 % 3 == 0 -> [6].
    check("boundary_single_day_hit",
          lambda: mod.occurrences(r3(), 6, 6) == [6])
    # window [7, 7]: 7 % 3 == 1 -> [].
    check("boundary_single_day_miss",
          lambda: mod.occurrences(r3(), 7, 7) == [])
    # start > end -> [] by definition.
    check("boundary_inverted_window",
          lambda: mod.occurrences(r3(), 10, 2) == [])
    # window [3, 8]: hits 3, 6 (start edge 3 included; 9 > 8 excluded).
    check("boundary_occurrence_at_start",
          lambda: mod.occurrences(r3(), 3, 8) == [3, 6])
    # window [1, 6]: hits 3, 6 (end edge 6 included; 0 < 1 excluded).
    check("boundary_occurrence_at_end",
          lambda: mod.occurrences(r3(), 1, 6) == [3, 6])
    # window [3, 9]: both edges are occurrences -> [3, 6, 9].
    check("boundary_both_edges_inclusive",
          lambda: mod.occurrences(r3(), 3, 9) == [3, 6, 9])
    # strictly after: 6 is itself an occurrence, next is 9.
    check("boundary_next_after_is_strict",
          lambda: mod.next_after(r3(), 6) == 9)
    # 4 is not an occurrence; next multiple of 3 above 4 is 6.
    check("boundary_next_after_between",
          lambda: mod.next_after(r3(), 4) == 6)
    # "monthly on 1" hits d % 30 == 0: 0, 30, 60; strictly after 59 -> 60.
    check("boundary_next_after_monthly_edge",
          lambda: mod.next_after(mod.parse_rule("monthly on 1"), 59) == 60)
    # "every 2000 weeks on mon": occurrences at day 0, then week 2000 =
    # day 14000. next_after(rule, 0) scans days 1..10001 -> none -> ValueError.
    check("boundary_next_after_none_raises",
          lambda: _raises_value_error(
              lambda: mod.next_after(
                  mod.parse_rule("every 2000 weeks on mon"), 0)))
    # zero-length window at day 0; day 0 is a Monday -> [0].
    check("boundary_window_zero_day",
          lambda: mod.occurrences(mod.parse_rule("weekly on mon"), 0, 0)
          == [0])
    return results
