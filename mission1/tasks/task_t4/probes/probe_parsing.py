"""Probe family: PARSING — precedence, associativity, unary minus, rejection.
Each probe returns (name, passed). Trusted code; organisms never see this."""


def _raises_ve(fn):
    try:
        fn()
    except ValueError:
        return True
    except Exception:
        return False
    return False


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    # 1+2*3: * binds tighter, so add(1, mul(2, 3)).
    check("parse_prec_mul_over_add",
          lambda: mod.parse("1+2*3") ==
          ("add", ("num", 1), ("mul", ("num", 2), ("num", 3))))
    # (1+2)*3: parens override precedence -> mul(add(1,2), 3).
    check("parse_prec_parens_override",
          lambda: mod.parse("(1+2)*3") ==
          ("mul", ("add", ("num", 1), ("num", 2)), ("num", 3)))
    # 1+2+3 is left-associative: (1+2)+3.
    check("parse_assoc_add_left",
          lambda: mod.parse("1+2+3") ==
          ("add", ("add", ("num", 1), ("num", 2)), ("num", 3)))
    # 2*3*4 is left-associative: (2*3)*4.
    check("parse_assoc_mul_left",
          lambda: mod.parse("2*3*4") ==
          ("mul", ("mul", ("num", 2), ("num", 3)), ("num", 4)))
    # x-y desugars: add(x, neg(y)) — no "sub" node exists.
    check("parse_sub_desugars",
          lambda: mod.parse("x-y") ==
          ("add", ("var", "x"), ("neg", ("var", "y"))))
    # 1-2-3 left-assoc = (1-2)-3, each '-' desugared:
    # add(add(1, neg(2)), neg(3)).
    check("parse_sub_left_assoc",
          lambda: mod.parse("1-2-3") ==
          ("add", ("add", ("num", 1), ("neg", ("num", 2))),
           ("neg", ("num", 3))))
    # Redundant nested parens vanish: ((x)) is just var x.
    check("parse_nested_parens",
          lambda: mod.parse("((x))") == ("var", "x"))
    # Chained unary minus: --x -> neg(neg(x)) (parse does NOT simplify).
    check("parse_unary_chain",
          lambda: mod.parse("--x") == ("neg", ("neg", ("var", "x"))))
    # Brief: unary minus binds tighter than *, so -x*y = (-x)*y.
    check("parse_unary_binds_tighter_than_mul",
          lambda: mod.parse("-x*y") ==
          ("mul", ("neg", ("var", "x")), ("var", "y")))
    # Malformed inputs must raise ValueError (and only ValueError).
    check("parse_malformed_empty",
          lambda: _raises_ve(lambda: mod.parse("")))
    check("parse_malformed_dangling_op",
          lambda: _raises_ve(lambda: mod.parse("1+")))
    check("parse_malformed_adjacent_operands",
          lambda: _raises_ve(lambda: mod.parse("2x")))
    check("parse_malformed_bad_char",
          lambda: _raises_ve(lambda: mod.parse("x/y")))
    check("parse_malformed_unknown_var",
          lambda: _raises_ve(lambda: mod.parse("a+b")))
    check("parse_malformed_unbalanced_paren",
          lambda: _raises_ve(lambda: mod.parse("(x+y")))
    return results
