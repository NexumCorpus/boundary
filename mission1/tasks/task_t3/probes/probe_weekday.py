"""Probe family: WEEKDAY MAPPING (area: weekday-mapping).
Day 0 is a Monday; weekday = d % 7 with 0=mon..6=sun. Weekly rules land ONLY
on declared weekdays; "every N weeks" keeps only weeks where (d//7) % N == 0.
Each probe returns (name, passed). Trusted code; organisms never see this."""


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    # Mondays are d % 7 == 0; in [0, 6] only day 0.
    check("weekday_day0_is_monday",
          lambda: mod.occurrences(mod.parse_rule("weekly on mon"), 0, 6)
          == [0])
    # Sundays are d % 7 == 6; in [0, 13]: 6 and 13.
    check("weekday_sunday_is_six",
          lambda: mod.occurrences(mod.parse_rule("weekly on sun"), 0, 13)
          == [6, 13])
    # mon(0)+thu(3) over [0, 20]: 0, 3, 7, 10, 14, 17 (21 > 20).
    check("weekday_mon_thu_three_weeks",
          lambda: mod.occurrences(mod.parse_rule("weekly on mon,thu"), 0, 20)
          == [0, 3, 7, 10, 14, 17])
    # tue(1)+fri(4) over [0, 69]: tue 1,8,...,64 (10 hits) and fri 4,11,...,67
    # (10 hits) -> 20 total, all with d % 7 in {1, 4}, first 1, last 67.
    def _only_declared():
        occ = mod.occurrences(mod.parse_rule("weekly on tue,fri"), 0, 69)
        return (len(occ) == 20 and occ[0] == 1 and occ[-1] == 67
                and all(d % 7 in (1, 4) for d in occ))
    check("weekday_only_declared_days", _only_declared)
    # tue over [10, 30]: tuesdays are 1,8,15,22,29,...; >=10 and <=30 ->
    # 15, 22, 29.
    check("weekday_midweek_window",
          lambda: mod.occurrences(mod.parse_rule("weekly on tue"), 10, 30)
          == [15, 22, 29])
    # all seven weekdays declared -> every day in the window.
    check("weekday_all_seven_days",
          lambda: mod.occurrences(
              mod.parse_rule("weekly on mon,tue,wed,thu,fri,sat,sun"), 3, 9)
          == [3, 4, 5, 6, 7, 8, 9])
    # every 2 weeks on fri: fridays are 4,11,18,25,32,39,46,53,60 with weeks
    # 0..8; keep even weeks -> 4, 18, 32, 46, 60.
    check("weekday_biweekly_friday",
          lambda: mod.occurrences(
              mod.parse_rule("every 2 weeks on fri"), 0, 60)
          == [4, 18, 32, 46, 60])
    # every 3 weeks on wed: wednesdays 2,9,16,23,30,37,44 have weeks
    # 0,1,2,3,4,5,6; keep weeks % 3 == 0 (0, 3, 6) -> 2, 23, 44.
    check("weekday_triweekly_wednesday",
          lambda: mod.occurrences(
              mod.parse_rule("every 3 weeks on wed"), 0, 50)
          == [2, 23, 44])
    # window [5, 17] contains exactly one friday: day 11 (week 1, odd) ->
    # excluded by the every-2-weeks filter -> [].
    check("weekday_biweekly_skips_odd_weeks",
          lambda: mod.occurrences(
              mod.parse_rule("every 2 weeks on fri"), 5, 17) == [])
    return results
