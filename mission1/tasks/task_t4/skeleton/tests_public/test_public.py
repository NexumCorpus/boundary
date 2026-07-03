import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simp import evaluate, parse, simplify, to_string


def test_parse_simple():
    assert parse("x+2") == ("add", ("var", "x"), ("num", 2))


def test_parse_precedence():
    assert parse("x+y*z") == (
        "add", ("var", "x"), ("mul", ("var", "y"), ("var", "z")))


def test_roundtrip():
    assert to_string(parse("x+y*z")) == "x+y*z"


def test_fold_constants():
    assert simplify(parse("2+3")) == ("num", 5)


def test_identity_add_zero():
    assert simplify(parse("x+0")) == ("var", "x")


def test_evaluate():
    assert evaluate(parse("x+2*y"), {"x": 1, "y": 3}) == 7
