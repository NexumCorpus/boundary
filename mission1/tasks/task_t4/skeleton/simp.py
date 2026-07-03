"""Expression simplifier over x, y, z with + - * and unary minus.

AST: ("num", n) | ("var", v) | ("add", a, b) | ("mul", a, b) | ("neg", a)
See brief.md for the full contract.
"""


def parse(text):
    """Parse text into an AST tuple. ValueError on malformed input."""
    raise NotImplementedError


def simplify(ast):
    """Return the canonical simplified AST (see brief.md)."""
    raise NotImplementedError


def to_string(ast):
    """Render an AST with minimal parentheses."""
    raise NotImplementedError


def evaluate(ast, env):
    """Evaluate an AST to an int using env: dict[str, int]."""
    raise NotImplementedError
