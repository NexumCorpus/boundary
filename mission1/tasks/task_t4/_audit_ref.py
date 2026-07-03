"""Audit reference implementation, derived from brief.md ONLY.

Faithful reading of the T4 brief. NOT derived from the probes.
"""

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_VARS = {"x", "y", "z"}


def _tokenize(text):
    toks = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            toks.append(("num", int(text[i:j])))
            i = j
            continue
        if c in "xyz":
            toks.append(("var", c))
            i += 1
            continue
        if c in "+-*()":
            toks.append((c, c))
            i += 1
            continue
        raise ValueError("bad char: %r" % c)
    return toks


class _Parser:
    def __init__(self, toks):
        self.toks = toks
        self.pos = 0

    def peek(self):
        if self.pos < len(self.toks):
            return self.toks[self.pos]
        return (None, None)

    def advance(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def parse(self):
        node = self.parse_add()
        if self.pos != len(self.toks):
            raise ValueError("trailing tokens")
        return node

    # add := mul (('+'|'-') mul)*   left-assoc, loosest
    def parse_add(self):
        node = self.parse_mul()
        while self.peek()[0] in ("+", "-"):
            op = self.advance()[0]
            rhs = self.parse_mul()
            if op == "+":
                node = ("add", node, rhs)
            else:
                node = ("add", node, ("neg", rhs))
        return node

    # mul := unary ('*' unary)*  left-assoc
    def parse_mul(self):
        node = self.parse_unary()
        while self.peek()[0] == "*":
            self.advance()
            rhs = self.parse_unary()
            node = ("mul", node, rhs)
        return node

    # unary := '-' unary | atom    (unary minus binds tighter than *, chainable)
    def parse_unary(self):
        if self.peek()[0] == "-":
            self.advance()
            return ("neg", self.parse_unary())
        return self.parse_atom()

    # atom := num | var | '(' add ')'
    def parse_atom(self):
        kind, val = self.peek()
        if kind == "num":
            self.advance()
            return ("num", val)
        if kind == "var":
            self.advance()
            return ("var", val)
        if kind == "(":
            self.advance()
            node = self.parse_add()
            if self.peek()[0] != ")":
                raise ValueError("expected )")
            self.advance()
            return node
        raise ValueError("unexpected token: %r" % (self.peek(),))


def parse(text):
    toks = _tokenize(text)
    if not toks:
        raise ValueError("empty")
    return _Parser(toks).parse()


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

def evaluate(ast, env):
    k = ast[0]
    if k == "num":
        return ast[1]
    if k == "var":
        return env[ast[1]]
    if k == "add":
        return evaluate(ast[1], env) + evaluate(ast[2], env)
    if k == "mul":
        return evaluate(ast[1], env) * evaluate(ast[2], env)
    if k == "neg":
        return -evaluate(ast[1], env)
    raise ValueError("bad node")


# ---------------------------------------------------------------------------
# Simplify
# ---------------------------------------------------------------------------
#
# Strategy per brief's recommended scheme:
#   - Represent an additive level as a dict/list of terms.
#   - Each term = coefficient * (sorted list of non-constant factors).
#   - Sort operand lists by str(canonical AST).
#   - Rebuild by left-folding.
#
# We build canonical ASTs bottom-up.

def _mk_add_list(terms):
    """terms: list of canonical ASTs to be summed. Left-fold after sorting
    by str()."""
    if not terms:
        return ("num", 0)
    terms = sorted(terms, key=lambda t: str(t))
    node = terms[0]
    for t in terms[1:]:
        node = ("add", node, t)
    return node


def _mk_mul_list(factors):
    if not factors:
        return ("num", 1)
    factors = sorted(factors, key=lambda t: str(t))
    node = factors[0]
    for f in factors[1:]:
        node = ("mul", node, f)
    return node


def _flatten_add(ast):
    """Return list of additive terms (each still raw, pre-simplify)."""
    if ast[0] == "add":
        return _flatten_add(ast[1]) + _flatten_add(ast[2])
    if ast[0] == "neg":
        # neg distributes over addition at the additive level
        inner = _flatten_add(ast[1])
        return [("neg", t) for t in inner]
    return [ast]


def _flatten_mul(ast):
    if ast[0] == "mul":
        return _flatten_mul(ast[1]) + _flatten_mul(ast[2])
    return [ast]


def _term_key(factors):
    """Canonical key for the non-constant factor bundle of a term."""
    return tuple(sorted(str(f) for f in factors))


def _simplify(ast):
    k = ast[0]

    if k in ("num", "var"):
        return ast

    if k == "neg":
        inner = _simplify(ast[1])
        if inner[0] == "num":
            return ("num", -inner[1])
        if inner[0] == "neg":
            return inner[1]  # neg(neg(e)) -> e
        # push neg into a term: represent as multiply-by-(-1) handled at add level
        return ("neg", inner)

    if k == "mul":
        factors_raw = _flatten_mul(ast)
        simp_factors = [_simplify(f) for f in factors_raw]
        # collect constant product and non-constant factors; track sign from negs
        const = 1
        nonconst = []
        for f in simp_factors:
            g = f
            # peel negs
            while g[0] == "neg":
                const = -const
                g = g[1]
            if g[0] == "num":
                const *= g[1]
            else:
                # g may itself be an add/mul canonical subtree; keep as factor
                nonconst.append(g)
        if const == 0:
            return ("num", 0)
        if not nonconst:
            return ("num", const)
        body = _mk_mul_list(nonconst)
        if const == 1:
            return body
        if const == -1:
            # represent -1 * body; canonical: use neg
            return ("neg", body)
        return _canon_coeff_times(const, body)

    if k == "add":
        terms_raw = _flatten_add(ast)
        simp_terms = [_simplify(t) for t in terms_raw]
        # Each simplified term: extract coefficient and factor-bundle.
        # bundle_key -> [coeff_sum, representative_factor_list]
        buckets = {}
        order = []
        const_sum = 0
        for t in simp_terms:
            coeff, factors = _term_to_coeff_factors(t)
            if not factors:
                const_sum += coeff
                continue
            key = _term_key(factors)
            if key not in buckets:
                buckets[key] = [0, factors]
                order.append(key)
            buckets[key][0] += coeff
        out_terms = []
        for key in order:
            coeff, factors = buckets[key]
            if coeff == 0:
                continue
            body = _mk_mul_list(factors)
            if coeff == 1:
                out_terms.append(body)
            elif coeff == -1:
                out_terms.append(("neg", body))
            else:
                out_terms.append(_canon_coeff_times(coeff, body))
        if const_sum != 0:
            out_terms.append(("num", const_sum))
        if not out_terms:
            return ("num", 0)
        return _mk_add_list(out_terms)

    raise ValueError("bad node")


def _canon_coeff_times(coeff, body):
    """Build canonical (num coeff) * body, respecting operand sort by str().
    coeff is an int, not 0/1/-1 (those handled elsewhere)."""
    return _mk_mul_list([("num", coeff), body])


def _term_to_coeff_factors(t):
    """Given a simplified term, return (coeff:int, factors:list-of-canonical).
    factors excludes the numeric coefficient."""
    # peel negs
    sign = 1
    while t[0] == "neg":
        sign = -sign
        t = t[1]
    if t[0] == "num":
        return (sign * t[1], [])
    if t[0] == "var":
        return (sign, [t])
    if t[0] == "mul":
        factors = _flatten_mul(t)
        const = 1
        nonconst = []
        for f in factors:
            g = f
            while g[0] == "neg":
                const = -const
                g = g[1]
            if g[0] == "num":
                const *= g[1]
            else:
                nonconst.append(g)
        return (sign * const, nonconst)
    # add subtree acting as a factor-bundle atom (e.g. (y+z))
    return (sign, [t])


def simplify(ast):
    return _simplify(ast)


# ---------------------------------------------------------------------------
# to_string
# ---------------------------------------------------------------------------

_PREC = {"add": 1, "mul": 2, "neg": 3, "num": 4, "var": 4}


def to_string(ast):
    k = ast[0]
    if k == "num":
        return str(ast[1])
    if k == "var":
        return ast[1]
    if k == "neg":
        s = _wrap(ast[1], 3)
        return "-" + s
    if k == "add":
        # a - b rendering when rhs is neg
        left = _wrap(ast[1], 1)
        if ast[2][0] == "neg":
            return left + "-" + _wrap(ast[2][1], 2)
        return left + "+" + _wrap(ast[2], 1)
    if k == "mul":
        return _wrap(ast[1], 2) + "*" + _wrap(ast[2], 2)
    raise ValueError("bad node")


def _wrap(child, parent_prec):
    cp = _PREC[child[0]]
    s = to_string(child)
    if cp < parent_prec:
        return "(" + s + ")"
    return s
