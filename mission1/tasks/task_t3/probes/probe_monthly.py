"""Probe family: MONTHLY ARITHMETIC (area: monthly-arithmetic).
30-day months: "monthly on N" hits exactly the days d with d % 30 == N - 1.
Each probe returns (name, passed). Trusted code; organisms never see this."""


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    m1 = lambda: mod.parse_rule("monthly on 1")     # d % 30 == 0
    m15 = lambda: mod.parse_rule("monthly on 15")   # d % 30 == 14
    m30 = lambda: mod.parse_rule("monthly on 30")   # d % 30 == 29

    # monthly on 1 over [0, 90]: 0, 30, 60, 90 (90 % 30 == 0, end inclusive).
    check("monthly_on_1_multiples",
          lambda: mod.occurrences(m1(), 0, 90) == [0, 30, 60, 90])
    # monthly on 15 over [0, 100]: 14, 44, 74 (104 > 100).
    check("monthly_on_15_span",
          lambda: mod.occurrences(m15(), 0, 100) == [14, 44, 74])
    # monthly on 30 over [0, 120]: 29, 59, 89, 119.
    check("monthly_on_30_last_day",
          lambda: mod.occurrences(m30(), 0, 120) == [29, 59, 89, 119])
    # unaligned window [20, 80] for monthly on 15: 14 < 20 excluded ->
    # 44, 74 (104 > 80).
    check("monthly_unaligned_window",
          lambda: mod.occurrences(m15(), 20, 80) == [44, 74])
    # window [15, 43] falls strictly between hits 14 and 44 -> [].
    check("monthly_window_between_hits",
          lambda: mod.occurrences(m15(), 15, 43) == [])
    # window edges exactly on hits: [14, 44] -> [14, 44].
    check("monthly_edges_inclusive",
          lambda: mod.occurrences(m15(), 14, 44) == [14, 44])
    # monthly on 30: 29 is a hit; strictly after 29 -> 59.
    check("monthly_next_after_hit",
          lambda: mod.next_after(m30(), 29) == 59)
    # monthly on 1: hits 0, 30, 60; strictly after 0 -> 30.
    check("monthly_next_after_start",
          lambda: mod.next_after(m1(), 0) == 30)
    # monthly on 15 hits 14, 44, 74, 104; strictly after 100 -> 104
    # (104 % 30 == 14).
    check("monthly_next_after_unaligned",
          lambda: mod.next_after(m15(), 100) == 104)
    return results
