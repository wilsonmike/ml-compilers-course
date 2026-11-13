# .uir, week 1 (provisional)

The official course promises "a universal, simple, interchange format for UOps" but has not
published a grammar yet. This is our own version, built from the two examples in the public
syllabus. When the official grammar ships we will migrate to it, and the tests will change with it.

The oracle (`_reference/uirc.py`) is the final word: the grader compares your compiler to the
oracle, not to the test headers. If this file and the oracle disagree, one of them has a bug.
File an issue.

## 1. Lexical rules

```
# a comment runs to the end of the line
%sum  = add 2 3
%test = assert %sum 5
```

* The file is UTF-8 (a BOM is allowed). Lines end in `\n` or `\r\n`. Whitespace means spaces and
  tabs, anywhere, including at the start of a line.
* One statement per line: `%name = op operand* attr*`. Blank lines and comment-only lines are fine.
* Names match `[A-Za-z0-9_]+`, ASCII only. A name must be defined above its first use, and defined once.
  Op names are lowercase.
* An operand is one of:

  | form | regex | meaning |
  |---|---|---|
  | reference | `%[A-Za-z0-9_]+` | an earlier statement |
  | integer | `-?[0-9]+` | a `const` of dtype `i32`. It must fit in 32 bits, or the program is invalid. |
  | float | `-?([0-9]+\.[0-9]*\|\.[0-9]+)([eE][-+]?[0-9]+)?` or `-?[0-9]+[eE][-+]?[0-9]+` | a `const` of dtype `f32` |
  | special float | `inf`, `-inf`, `nan` | a `const` of dtype `f32` |
  | bool | `true`, `false` | a `const` of dtype `bool` |

  Nothing else is a literal: no leading `+`, no hex, no `_` separators, no `infinity`.
  A float literal is read as a 64-bit double, then rounded to f32 (round to nearest-even).
  Too big for f32 rounds to `inf`; too small rounds to `0.0`. That's what OCaml's
  `float_of_string` followed by an f32 rounding does, so it's easy to match.
* Attributes are `key=value`, written **after** all operands, with no spaces around `=`.
  Each op accepts only the attributes listed in section 3. An unknown attribute, a repeated
  attribute, or an attribute before an operand makes the program invalid.
  A list value is `[k]`: one integer, `k >= 1`, in week 1.

## 2. Values

Every UOp has a **dtype** and a **shape**.

| dtype | meaning |
|---|---|
| `void` | no value. Only `assert` produces it, and it can't be an operand. |
| `bool` | `true` / `false` |
| `i32`  | 32-bit two's complement. `add`, `mul` and `shl` wrap around. |
| `f32`  | IEEE-754 binary32, rounded to nearest-even after every op |

A shape is a tuple of ints. In week 1 the rank is at most 1: either `()` (a scalar) or `(n,)`.

There is **no implicit type conversion**. `add %x 1` where `%x` is `f32` is a type error. Write
`add %x 1.0`, or use `cast`.

## 3. Ops

`a`, `b`, `c` are operands. "num" means `i32` or `f32`.

**ALU ops** are `cast recip add mul max xor cmplt shl div mod where`. Every operand of an ALU op
must have shape `()`.

| op | attributes | operands | result | notes |
|---|---|---|---|---|
| `const v` | `dtype` (optional) | one literal | D, `()` | `const v dtype=D` means `cast v dtype=D`, except a float literal can't become `i32` or `bool`. The literal must still be valid on its own. |
| `param n` | `dtype` (required), `shape` (optional) | slot n ≥ 0 | D, shape | Input slot n of the enclosing `call`. |
| `call f a0 a1 ...` | none | body, args | body's | Arg i binds `param i` inside `f`. See section 4. |
| `stack a0 a1 ...` | none | ≥1 scalars, same dtype | same, `(n,)` | Adds a new leading axis. |
| `index x i` | none | x of shape `(n,)`, i is `i32` `()` | `()` | Element i. Out of range (i < 0 or i ≥ n) is a runtime error. |
| `cast a` | `dtype` (required) | any non-void scalar | D | See section 5. |
| `recip a` | none | f32 | f32 | `1/a`. `recip 0.0 = inf`, `recip -0.0 = -inf`. |
| `add a b`, `mul a b` | none | num, same dtype | same | |
| `max a b` | none | num, same dtype | same | f32: NaN if either is NaN, and `max(-0.0, 0.0) = +0.0` in either order. |
| `xor a b` | none | i32 or bool, same dtype | same | Bitwise for i32, logical for bool. |
| `cmplt a b` | none | num, same dtype | bool | `a < b`. Any NaN gives false. |
| `shl a b` | none | i32 | i32 | `a << b`, wraps. b outside [0, 31] is a runtime error. |
| `div a b` | none | i32 | i32 | Truncates toward zero, like C. `b = 0` is a runtime error. `INT_MIN / -1 = INT_MIN`. |
| `mod a b` | none | i32 | i32 | `a - (a div b) * b`, so the sign follows `a`, like C. `b = 0` is a runtime error. `INT_MIN mod -1 = 0`. |
| `where c a b` | none | c bool, a and b same dtype | a's | `a` if `c`, else `b`. Strict: both branches are evaluated. |
| `assert a b` | none | same dtype and shape | void | Passes if `a` equals `b`, elementwise. |

Equality for `assert`: i32 and bool compare exactly. f32 compares by value, so `0.0 == -0.0`, and two
NaNs count as equal.

## 4. call and param

```
%x    = param 0 dtype=i32
%body = add %x 1          # a function body: "x + 1"
%r    = call %body 41     # bind param 0 := 41
%t    = assert %r 42
```

* `call f a0 a1 ...` evaluates `f` with every `param i` reachable from `f` replaced by `ai`.
* **Bodies are closed.** Substitution does not descend into the body (src 0) of a nested `call`.
  It does go into that call's args. That's how you pass values inward:
  ```
  %p0    = param 0 dtype=i32
  %inner = mul %p0 2        # inner's own param 0
  %outer = call %inner %p0  # outer passes ITS param 0 into inner's slot 0
  %r     = call %outer 5    # 10
  ```
* Every param reachable from the body must have an arg with a matching dtype and shape. Extra args
  are allowed. This is a static (type) check.
* A call evaluates all of its args before the body, extra ones included. So `call %b 1 %e` with
  `%e = div 1 0` is a runtime error (exit 2) when an assert needs it, even if `%b` has no `param 1`.
* One slot used with two different types in the same expression is a static error, whether or
  not anything calls it.
* A `param` evaluated outside any call is a runtime error.

UOps are hash consed: two statements with the same op, sources and arg, where dtype and shape are
part of the key, are *the same node*. Compare float args by bit pattern, so `0.0` and `-0.0` stay
different nodes. `%a = param 0 dtype=i32` and `%b = param 0 dtype=i32` are one UOp, and that's
fine, because what a param means depends on which call is evaluating it.

## 5. cast

| from → to | rule |
|---|---|
| same dtype | identity |
| bool → i32 / f32 | 0 or 1 |
| i32 / f32 → bool | `a != 0` (NaN → true) |
| i32 → f32 | round to nearest-even |
| f32 → i32 | truncate toward zero. NaN, ±inf, or a result outside the i32 range, is a runtime error. |
| anything ↔ void | type error |

## 6. Evaluation

1. **Every statement is parsed and type checked first**, whether or not anything uses it. Any parse
   or type error makes the program invalid (exit 2), even if an earlier assert would fail.
2. Then the **asserts run in file order**. The first assert that fails stops the program (exit 1).
   The first assert whose value hits a runtime error stops it (exit 2). Later asserts never run.
3. A statement no assert depends on is never evaluated, so its runtime errors don't matter.
4. Evaluation must reuse shared work. A DAG with a lot of sharing (`%x2 = add %x1 %x1`, repeated
   300 times) has to finish in milliseconds.

## 7. Command line contract

Your compiler is one executable with two subcommands. Grade the built executable directly
(`_build/default/bin/main.exe`), not `dune exec`: the grader runs tests in parallel, and parallel
`dune exec` runs fight over dune's lock. `--jobs 1` makes the grader run tests one at a time.

### `run FILE`

| exit | stderr must contain | meaning |
|---|---|---|
| 0 | anything | every assert passed |
| 1 | exactly one line `assert failed: %name`, naming the first failing assert | an assert failed |
| 2 | a line starting with `invalid:` | invalid program: a parse error, type error, undefined name, or a runtime error in a value an assert depends on |

An uncaught exception is not a diagnosis. OCaml exits 2 on `Fatal error: exception ...`, but without
an `invalid:` line the grader fails the test.

The tests never hide an error behind an absorbing op like `mul (div 1 0) 0`, so a simplifier that
folds that to `0` before running is not penalised.

### `simplify FILE`

FILE defines `%out`, usually over params, and has no asserts. Print a valid .uir program to stdout
that defines `%out`, with the same dtype and shape. It must compute the same value for every input
where the original doesn't error. The grader:

1. parses your output with the oracle
2. counts the **ops in your text**: every `%name = op` statement reachable from `%out`, except
   `const` and `param`. Duplicate statements count separately, so hash cons your output. The count
   must be at most the test's `max_ops`.
3. calls both versions on every edge value in every param slot (the full cross product when there
   are 1 or 2 params), plus random values, including `INT_MIN`, `INT_MAX`, `-0.0`, `±inf`, `nan`,
   subnormals and the largest f32. Results must match **bit for bit** for f32, so `0.0` and `-0.0`
   differ. Any NaN matches any NaN.

Bugs this catches: `x * 0.0 → 0.0` (`nan * 0.0` is `nan`), `x + 0.0 → x` (`-0.0 + 0.0` is `+0.0`),
and `(x * 2) / 2 → x` on i32 (it wraps). `x + -0.0 → x` is correct.

**Printing f32 constants.** Print enough digits to round-trip (`%.9g` is enough for any f32) and
always include a `.` or an `e`, or the literal reads back as an i32. Print `inf`, `-inf` and `nan`
exactly like that. In OCaml, `Printf.sprintf "%.9g" x`, then append `.0` if the result has no `.`,
`e`, `n` or `i`.

## 8. Test file headers

```
# expect: pass          (or assert_fail, or invalid)
# simplify: max_ops=1   (simplify tests only)
```

The grader copies each test to a neutral file name before running your compiler, so the name of
a test file tells your compiler nothing.
