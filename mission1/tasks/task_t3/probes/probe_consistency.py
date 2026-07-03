"""Probe family: CROSS-FUNCTION CONSISTENCY (area: cross-function-consistency).
count_in == len(occurrences); next_after lands inside occurrences and is
strictly greater; occurrences is sorted strictly increasing; deterministic.
Each probe returns (name, passed). Trusted code; organisms never see this."""


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    rw = lambda: mod.parse_rule("weekly on mon,thu")
    r4 = lambda: mod.parse_rule("every 4 days")
    m15 = lambda: mod.parse_rule("monthly on 15")

    # count_in must equal len(occurrences) on the same window.
    check("consistency_count_eq_len_weekly",
          lambda: mod.count_in(rw(), 0, 50)
          == len(mod.occurrences(rw(), 0, 50)))
    check("consistency_count_eq_len_monthly",
          lambda: mod.count_in(m15(), 7, 200)
          == len(mod.occurrences(m15(), 7, 200)))
    # every 4 days hits 0,4,8,12,16,...; [13, 15] contains none -> 0 == 0.
    check("consistency_count_eq_len_empty",
          lambda: mod.count_in(r4(), 13, 15)
          == len(mod.occurrences(r4(), 13, 15)) == 0)

    # every 4 days: next after 10 is 12; 12 must appear in a containing
    # window's occurrences and be > 10.
    def _next_in_window():
        n = mod.next_after(r4(), 10)
        return n > 10 and n in mod.occurrences(r4(), 0, 40)
    check("consistency_next_in_window", _next_in_window)

    # strict inequality for every start day 0..20.
    check("consistency_next_strictly_greater",
          lambda: all(mod.next_after(r4(), d) > d for d in range(0, 21)))

    # weekly mon,thu over [0, 60]: mon 0,7,...,56 (9 hits) + thu 3,10,...,59
    # (9 hits) = 18 occurrences, sorted strictly increasing.
    def _sorted_strict():
        occ = mod.occurrences(rw(), 0, 60)
        return (len(occ) == 18
                and all(b > a for a, b in zip(occ, occ[1:])))
    check("consistency_sorted_strictly_increasing", _sorted_strict)

    # same inputs -> same outputs, twice.
    def _deterministic():
        a1 = mod.occurrences(rw(), 0, 60)
        a2 = mod.occurrences(rw(), 0, 60)
        c1 = mod.count_in(rw(), 0, 60)
        c2 = mod.count_in(rw(), 0, 60)
        return a1 == a2 and c1 == c2
    check("consistency_deterministic_calls", _deterministic)

    # chaining next_after from 0 on "every 5 days" yields 5, 10, 15 — the
    # same list occurrences gives over [1, 15].
    def _chain():
        r5 = mod.parse_rule("every 5 days")
        chain, d = [], 0
        for _ in range(3):
            d = mod.next_after(r5, d)
            chain.append(d)
        return chain == [5, 10, 15] == mod.occurrences(r5, 1, 15)
    check("consistency_next_chain_matches", _chain)
    return results
