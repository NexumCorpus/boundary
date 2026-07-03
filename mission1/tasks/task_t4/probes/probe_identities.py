"""Probe family: IDENTITIES — additive/multiplicative units, zero, double
negation, self-cancellation. Brief requires the exact minimal AST.
Trusted code; organisms never see this."""

X = ("var", "x")


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    # e+0 -> e (brief: exact minimal AST).
    check("ident_add_zero", lambda: mod.simplify(mod.parse("x+0")) == X)
    # 0+e -> e.
    check("ident_zero_add", lambda: mod.simplify(mod.parse("0+x")) == X)
    # e*1 -> e.
    check("ident_mul_one", lambda: mod.simplify(mod.parse("x*1")) == X)
    # 1*e -> e.
    check("ident_one_mul", lambda: mod.simplify(mod.parse("1*x")) == X)
    # e*0 -> ("num", 0).
    check("ident_mul_zero",
          lambda: mod.simplify(mod.parse("x*0")) == ("num", 0))
    # 0*e -> ("num", 0).
    check("ident_zero_mul",
          lambda: mod.simplify(mod.parse("0*x")) == ("num", 0))
    # neg(neg(e)) -> e, fed as a raw AST (not via parse).
    check("ident_neg_neg",
          lambda: mod.simplify(("neg", ("neg", X))) == X)
    # x-x -> ("num", 0): like-term cancellation to the additive unit.
    check("ident_sub_self",
          lambda: mod.simplify(mod.parse("x-x")) == ("num", 0))
    return results
