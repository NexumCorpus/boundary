"""Probe family: hapax (area hapax). Hand-derived oracle."""


def run(mod):
    r = []

    def chk(name, fn):
        try:
            r.append((name, bool(fn())))
        except Exception:
            r.append((name, False))

    # occurs-once only, alphabetical
    chk("basic", lambda: mod.hapax("red red blue green") == ["blue", "green"])
    chk("none_when_all_repeat", lambda: mod.hapax("a a b b") == [])
    chk("all_hapax_sorted", lambda: mod.hapax("charlie alpha bravo")
        == ["alpha", "bravo", "charlie"])
    chk("empty_text", lambda: mod.hapax("") == [])
    # case-folded before counting: "The the" -> both "the", not hapax
    chk("casefolded", lambda: mod.hapax("The the once") == ["once"])
    return r
