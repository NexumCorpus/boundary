"""Probe family: CONSTANT FOLDING — pure-constant trees of depth >= 3 must
collapse to a single ("num", n). Trusted code; organisms never see this."""


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    def folds(text, n):
        return mod.simplify(mod.parse(text)) == ("num", n)

    # 2+3*4: 3*4 = 12; 2+12 = 14.  Tree add(2, mul(3,4)), depth 3.
    check("fold_add_mul", lambda: folds("2+3*4", 14))
    # (1+2)*(3+4): 3*7 = 21.  mul(add,add), depth 3.
    check("fold_paren_products", lambda: folds("(1+2)*(3+4)", 21))
    # -(2+3)*4: unary minus applies to (2+3): (-5)*4 = -20.
    check("fold_neg_group", lambda: folds("-(2+3)*4", -20))
    # 2*3-30: 6 - 30 = -24 (negative result must fold too).
    check("fold_negative_result", lambda: folds("2*3-30", -24))
    # 1+2*(3+4*5): 4*5=20; 3+20=23; 2*23=46; 1+46=47.  Depth 4.
    check("fold_deep_nest", lambda: folds("1+2*(3+4*5)", 47))
    # -(-(7)): double negation of a constant -> 7.
    check("fold_double_neg_const", lambda: folds("-(-(7))", 7))
    return results
