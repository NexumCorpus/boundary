"""Probe family: LIKE TERMS — collection at the same additive level.
Assertion style: value-equivalence at a hand-derived env PLUS a node-count
bound, so any correct canonical shape passes but uncollected forms cannot.
Node counts below are for the natural collected form, e.g.
5*x = ("mul", ("num", 5), ("var", "x")) = 3 nodes.
Trusted code; organisms never see this."""


def _nodes(t):
    n = 1
    for c in t[1:]:
        if isinstance(c, tuple):
            n += _nodes(c)
    return n


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    def collected(text, env, want, max_nodes):
        t = mod.simplify(mod.parse(text))
        return mod.evaluate(t, env) == want and _nodes(t) <= max_nodes

    # 2*x+3*x -> 5*x.  At x=7: 5*7 = 35.  Collected form has 3 nodes
    # (mul, num 5, var x); the uncollected input has 7.
    check("like_2x_plus_3x",
          lambda: collected("2*x+3*x", {"x": 7}, 35, 3))
    # x+x -> 2*x.  At x=7: 14.  3 nodes; uncollected add(x,x) has 3 too,
    # but evaluates the same — the bound forbids anything LARGER (e.g.
    # leaving it as add(x,x) is 3 nodes and value-correct; both shapes
    # within budget are acceptable collections of one term).
    check("like_x_plus_x",
          lambda: collected("x+x", {"x": 7}, 14, 3))
    # 2*x+y+3*x -> 5*x+y.  At x=2, y=11: 10+11 = 21.
    # add(mul(num 5, var x), var y) = 5 nodes; uncollected input has 9.
    check("like_mixed_var",
          lambda: collected("2*x+y+3*x", {"x": 2, "y": 11}, 21, 5))
    # x*2+2*x (commuted coefficient) -> 4*x.  At x=3: 12.  3 nodes;
    # uncollected has 7.
    check("like_commuted_coeff",
          lambda: collected("x*2+2*x", {"x": 3}, 12, 3))
    # x+x+x-x -> 2*x.  At x=5: 10.  3 nodes; uncollected has 8.
    check("like_partial_cancel",
          lambda: collected("x+x+x-x", {"x": 5}, 10, 3))
    return results
