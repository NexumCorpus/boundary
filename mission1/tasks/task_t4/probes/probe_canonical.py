"""Probe family: CANONICAL FORM — structurally different but mathematically
equal expressions must simplify to the IDENTICAL tuple.  Each check also
pins the value at env x=2, y=3, z=5 (hand-derived below) so a degenerate
"collapse everything to one constant" simplifier cannot pass.
Trusted code; organisms never see this."""

ENV = {"x": 2, "y": 3, "z": 5}


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    def same(a, b, want):
        ta = mod.simplify(mod.parse(a))
        tb = mod.simplify(mod.parse(b))
        return ta == tb and mod.evaluate(ta, ENV) == want

    # x+y == y+x.  At env: 2+3 = 5.
    check("canon_add_commute", lambda: same("x+y", "y+x", 5))
    # (x+1)+y == y+x+1 (flattening + reordering).  2+1+3 = 6.
    check("canon_add_flatten", lambda: same("(x+1)+y", "y+x+1", 6))
    # x*y == y*x.  2*3 = 6.
    check("canon_mul_commute", lambda: same("x*y", "y*x", 6))
    # 2*x+y == y+x*2 (coefficient position + term order).  4+3 = 7.
    check("canon_coeff_position", lambda: same("2*x+y", "y+x*2", 7))
    # x*(y+z) == (z+y)*x — no expansion required, but the inner sum and
    # the factor order must both normalize.  2*(3+5) = 16.
    check("canon_factored_sum", lambda: same("x*(y+z)", "(z+y)*x", 16))
    # x-y == -y+x (subtraction desugars, then terms reorder).  2-3 = -1.
    check("canon_sub_commute", lambda: same("x-y", "-y+x", -1))
    return results
