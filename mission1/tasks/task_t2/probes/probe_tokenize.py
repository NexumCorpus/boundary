"""Probe family: tokenization (area tokenization). Hand-derived oracle."""


def run(mod):
    r = []

    def chk(name, fn):
        try:
            r.append((name, bool(fn())))
        except Exception:
            r.append((name, False))

    chk("empty", lambda: mod.tokens("") == [])
    chk("lowercased", lambda: mod.tokens("The CAT") == ["the", "cat"])
    chk("punct_separates", lambda: mod.tokens("a,b;c") == ["a", "b", "c"])
    chk("digits_are_tokens", lambda: mod.tokens("v2 go v2") == ["v2", "go", "v2"])
    chk("unicode_letters", lambda: mod.tokens("Café café")
        == ["café", "café"])
    chk("underscore_separates", lambda: mod.tokens("a_b") == ["a", "b"])
    chk("mixed_whitespace", lambda: mod.tokens("a\t b\nc") == ["a", "b", "c"])
    return r
