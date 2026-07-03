# Task T4: expression simplifier

Implement `simp.py` in this directory: a parser, canonical simplifier,
printer, and evaluator for arithmetic expressions over the variables
`x`, `y`, `z` with integer constants, the binary operators `+`, `-`, `*`,
unary minus, and parentheses.

## AST

Nested tuples, and nothing else:

- `("num", n)` — integer constant (Python `int`)
- `("var", v)` — variable, `v` in `{"x", "y", "z"}`
- `("add", a, b)` — addition
- `("mul", a, b)` — multiplication
- `("neg", a)` — unary negation

There is NO `"sub"` node: `a - b` parses to `("add", a, ("neg", b))`.

## Functions

### `parse(text) -> ast`

- Number literals are non-negative digit runs; negative values are written
  with unary minus.
- Standard precedence and associativity: binary `+`/`-` bind loosest and are
  left-associative (`1-2-3` == `(1-2)-3`); `*` binds tighter and is
  left-associative; unary minus binds tighter than `*` (`-x*y` == `(-x)*y`,
  as in Python) and may be chained (`--x`).
- Whitespace between tokens is ignored.
- Raise `ValueError` on ANY malformed input: empty input, unbalanced
  parentheses, dangling operators (`"1+"`), unknown characters or variables
  (only `x`, `y`, `z` exist), and adjacent operands with no operator
  (`"2x"` — there is no implicit multiplication).

### `simplify(ast) -> ast`

Return a canonical simplified AST. Required, at minimum:

- **Constant folding** — any pure-constant subtree becomes a single
  `("num", n)`.
- **Identities** — `e+0 -> e`, `0+e -> e`, `e*1 -> e`, `1*e -> e`,
  `e*0 -> ("num", 0)`, `neg(neg(e)) -> e`. The result is the exact minimal
  AST: `simplify(parse("x+0")) == ("var", "x")`.
- **Like terms** — collect terms at the same additive level:
  `2*x + 3*x -> 5*x`, `x + x -> 2*x`, `x - x -> ("num", 0)`.
- **Canonical form** — flatten `+` and `*` chains and normalize ordering so
  that structurally different but mathematically equal expressions simplify
  to the IDENTICAL tuple (e.g. `simplify(parse("x+y")) ==
  simplify(parse("y+x"))`). Recommended scheme: treat each additive level as
  a list of `coefficient * factors` terms; sort operand lists (factors within
  a product, terms within a sum) by the string form `str(operand)` of their
  canonical ASTs; rebuild by left-folding. Distribution/expansion of products
  over sums is NOT required (`x*(y+z)` may stay a product), but equal
  spellings of the same product/sum must converge.
- `simplify` must be **idempotent** (`simplify(simplify(t)) == simplify(t)`)
  and must preserve value: for every env, `evaluate(simplify(t), env) ==
  evaluate(t, env)`.

### `to_string(ast) -> str`

Render the AST with minimal parentheses: parentheses only where needed to
preserve structure under the precedence rules above (`x+y*z` round-trips
with no parentheses; `("mul", ("add", ...), ...)` needs them).
`("add", a, ("neg", b))` may render as `a-b`.

### `evaluate(ast, env) -> int`

`env` maps variable names to ints. Exact integer arithmetic.

## Running the public tests

    python -m pytest tests_public/ -q

## Correctness areas

- `parsing`
- `constant-folding`
- `identities`
- `like-terms`
- `canonical-form`
- `eval-equivalence`
