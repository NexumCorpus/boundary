"""Probe family: apostrophes (area apostrophes). Trusted oracle — hand-derived."""


def run(mod):
    r = []

    def chk(name, fn):
        try:
            r.append((name, bool(fn())))
        except Exception:
            r.append((name, False))

    # internal apostrophe kept: "don't" -> one token
    chk("internal_ascii", lambda: mod.tokens("don't") == ["don't"])
    # unicode apostrophe U+2019 internal kept
    chk("internal_unicode", lambda: mod.tokens("can’t") == ["can’t"])
    # bounding apostrophes stripped: "'hi'" -> "hi"
    chk("bounding_stripped", lambda: mod.tokens("'hi'") == ["hi"])
    # apostrophe not between alnums separates: "x' 'y" -> ["x","y"]
    chk("bounding_between_words", lambda: mod.tokens("x' 'y") == ["x", "y"])
    # multiple internal: "y'all'd" stays one token (both internal)
    chk("multi_internal", lambda: mod.tokens("y'all'd") == ["y'all'd"])
    # trailing apostrophe stripped: "dogs'" -> "dogs"
    chk("trailing_stripped", lambda: mod.tokens("dogs'") == ["dogs"])
    return r
