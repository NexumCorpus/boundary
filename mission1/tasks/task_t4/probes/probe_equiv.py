"""Probe family: EVAL EQUIVALENCE — simplify must preserve value on
randomized expressions, and must be idempotent.  The generator is
deterministic (random.Random(20260703)): every scored organism sees the
same 8 expressions and the same 5 environments.
Trusted code; organisms never see this."""

import random

_DEPTH = 4


def _gen(rng, depth):
    """Fully parenthesized random expression string: always unambiguous
    under the task grammar.  Coefficients in -5..5; negatives are emitted
    as "(-n)" which parses as neg(num n)."""
    if depth == 0 or rng.random() < 0.3:
        if rng.random() < 0.5:
            n = rng.randint(-5, 5)
            return "({0})".format(n) if n < 0 else str(n)
        return rng.choice("xyz")
    op = rng.choice(["+", "-", "*", "neg"])
    if op == "neg":
        return "(-" + _gen(rng, depth - 1) + ")"
    return "(" + _gen(rng, depth - 1) + op + _gen(rng, depth - 1) + ")"


def _exprs():
    rng = random.Random(20260703)
    return [_gen(rng, _DEPTH) for _ in range(8)]


def _envs():
    out = []
    for j in range(5):
        er = random.Random(9000 + j)
        out.append({v: er.randint(-10, 10) for v in "xyz"})
    return out


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    exprs = _exprs()
    envs = _envs()

    for i, s in enumerate(exprs):
        def equiv(s=s):
            raw = mod.parse(s)
            simp = mod.simplify(raw)
            return all(mod.evaluate(simp, env) == mod.evaluate(raw, env)
                       for env in envs)

        def idem(s=s):
            t = mod.simplify(mod.parse(s))
            return mod.simplify(t) == t

        check("equiv_expr_{0}".format(i), equiv)
        check("idem_expr_{0}".format(i), idem)
    return results
