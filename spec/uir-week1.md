# .uir, week 1

This is the official 10-411 week 1 format, from the course's
[week 1 reference](https://10-411.com/assignments/week1.pdf) (a draft). Everything here follows that PDF. Where the PDF
is silent or could be read two ways, this file says how we read it, marked **Our reading**. If the official course
settles one of those differently, we change to match.

The oracle (`_reference/uirc.py`) is the final word for the tests: the grader compares your compiler to the oracle,
not to this text. If this file and the oracle disagree, one of them has a bug. File an issue.

## 1. A program is a graph

```
%x = param [] slot=0 dtype=i32 addrspace=ALU
%s = add %x %x
%v = call %s 3
%t = assert %v 6
```

Each name is defined once and refers to the same value wherever it is used. A **UOp** is a triple
`(op, src, arg)`: the operation, its ordered sources, and data that isn't a node (like `slot=0`). Matching triples
are the same node: `%y = add %x %x` would name the very node `%s` names. That's **hash consing**.

The call binds slot 0 to 3, so its body computes 3 + 3 = 6, and the assert checks that.

## 2. Tokens

| token | example | meaning |
|---|---|---|
| DEF | `%x=` | A definition. `%x=` and `%x =` are both one token (any whitespace, newlines too, may sit before the `=`). |
| REF | `%x`, `%0` | A defined name: `%` and then one or more ASCII letters, digits or underscores. |
| INT | `-7`, `0xff` | Decimal `-?[0-9]+` or hex `0x[0-9a-fA-F]+`. Leading zeros are allowed (`007` is 7). |
| BOOL | `false` | `true` and `false`. |
| OP | `add` | A lowercase opcode from section 5. A constant is written as its literal, never as `const`. |
| ATTR | `slot=0` | One `key=value` token, no spaces inside. |
| `[` `]` | `[3 6]` | Brackets enclose stack elements. |
| EOF | | The end of the file. |

UIR is case-sensitive ASCII. A comment runs from `#` to the end of the line, and only there may other characters
appear. Outside comments, every character is printable ASCII or whitespace (space, tab, carriage return, newline),
so a byte-order mark or a control character makes the file invalid. A newline is just whitespace: a binding may span
lines, and several may share one. A comment can't sit between a name and its `=`.

**Our reading:** every integer literal must fit in i32, so `2147483648` and `0x80000000` are rejected. Hex has no
sign (`-0x10` is not a literal) and the prefix is a lowercase `0x`. A slot is a number, so `slot=00` and `slot=0`
are the same attribute and give the same node.

## 3. Grammar

```
file    := binding+ EOF
binding := DEF rhs
rhs     := OP atom* ATTR* | atom
atom    := REF | INT | BOOL | '[' atom* ']'
```

* Attributes follow all sources. Keys are unique and unordered.
* `rhs := atom` names a value directly: `%x = 5`, `%y = %x`, `%v = [10 20 30]`.
* A bracket atom is a stack: `[1 2]` and `stack 1 2` build the same node. `[]`, with no sources, is the scalar
  shape marker: dtype `void`, shape `()`.
* A name must be defined above its first use.

## 4. Values

Every node has a **dtype**, a **shape**, **bounds** and a **cost**.

| dtype | meaning |
|---|---|
| `i32` | 32-bit two's complement. Values wrap on overflow. |
| `bool` | `true` / `false`. As a number it is 0 or 1. |
| `void` | No value: `[]` and `assert`. Never an operand of an ALU op. |

In week 1 every shape has rank 0 (a scalar, `()`) or rank 1 (a vector, `(n,)`). ALU ops take scalars.
Every week 1 value lives in `addrspace=ALU`.

**Bounds** are an interval `[lo, hi]` that every value of the node is guaranteed to lie in, endpoints included.
`I` is the full i32 range. Bounds are worked out statically, op by op, with the rules in section 5. They decide
whether an `index` is safe and whether a call's arguments fit their params' limits.

* A hull runs from min to max: `hull{2, 5, 3} = [2, 5]`.
* i32: bounds that overflow i32 widen to `I`.
* bool: only zero is `[0, 0]`, never zero is `[1, 1]`, otherwise `[0, 1]`. ("Normalized to bool.")

## 5. The operation reference

`x` is in `[a, b]` and `y` is in `[c, d]`. **Same** means every input and the result share the dtype (or shape).
**N** is the number of result elements.

| op | meaning and arguments | dtype | shape | bounds | cost |
|---|---|---|---|---|---|
| const | A literal `v`, like `7` or `true`. No sources. | type of `v` | `()` | `[v, v]` | 0 |
| param | Shape `s`, then optional limits `L`. `slot=k` (unsigned decimal), `dtype=t`, `addrspace=ALU`. Week 1 requires shape `[]`. | `t` | decode `s` | `L` is `[l h]`, two literals of type `t` with `l <= h`. Default `I`. | 0 |
| call | Body `f`, then arguments from slot 0. Unused slots are allowed. | `Tf` | `Sf` | `Bf` | 1 + C(f) |
| stack | Add a leading axis. `stack 1 2` and `[1 2]` build the same node. | same | `(n,) + S` | hull of the element bounds | N |
| `[]` | No sources: the scalar shape marker. | void | `()` | `I` | 1 |
| index | `v` at k >= 1 scalar i32 indices. Each index must fit its axis. | `Tv` | `Sv[k:]` | `Bv` | 1 |
| cast | Convert `x` to `dtype=t`. | `t` | same | `Bx`, normalized to `t` | N |
| add | `x + y` | same | same | `[a + c, b + d]` | N |
| mul | `x * y` | same | same | `hull{ac, ad, bc, bd}` | N |
| max | The larger of `x` and `y`. | same | same | `[max(a, c), max(b, d)]` | N |
| div | Floor quotient `floor(x / y)`; -1 when `y = 0`. | i32 | same | For a fixed `y`, the hull of the endpoint quotients. Otherwise `I`. | N |
| mod | Remainder `x - y * floor(x / y)`; `x` when `y = 0`. | i32 | same | A `y` that isn't fixed: `I`. A fixed 0: `Bx`. A fixed nonzero `y`: the hull of the endpoint remainders if the endpoints' floor quotients agree, else `[0, y - 1]` (for `y > 0`) or `[y + 1, 0]` (for `y < 0`). | N |
| xor | Bitwise exclusive or of `x` and `y`. | same | same | Exact for two singletons; otherwise `I`. | N |
| shl | Shift `x` left by `k = y mod 32`. | i32 | same | The hull of `a * 2^k` and `b * 2^k` over the possible `k`. | N |
| cmplt | Is `x < y`? Needs `Tx = Ty`. | bool | same | `[1, 1]` if `b < c`; `[0, 0]` if `a >= d`; else `[0, 1]`. | N |
| where | Bool `p` picks `x` if true, `y` if false. Needs `Tx = Ty`. | `Tx` | same | The chosen side's bounds for a fixed `p`; else the hull of both. | N |
| assert | Compare `x` with an expected literal, or a stack of literals, of the same dtype and shape. | void | same | `I` | 0 |

"Fixed" means the bounds are a single value, like `[3, 3]`.

Notes on the semantics:

* `add`, `mul` and `shl` wrap: the result is the low 32 bits, read as two's complement.
* `div` floors, unlike C, which truncates: `div -7 2` is -4 and `mod -7 2` is 1. A nonzero `mod` has the sign of
  `y`. `div x 0` is -1 and `mod x 0` is `x`, so neither can fail. `div INT_MIN -1` is 2^31, which wraps to `INT_MIN`,
  and `mod INT_MIN -1` is 0.
* `shl x y` shifts by `y mod 32`, which is always 0 to 31: `shl 1 32` is 1 and `shl 1 -1` is `INT_MIN`.
* `cast` to bool is `x != 0`. `cast` from bool gives 0 or 1. Casting to the same dtype changes nothing.
* `where` evaluates both sides. Nothing in week 1 can fail at run time, so that's never visible.
* **Our reading:** `add`, `mul`, `max`, `xor` and `cmplt` take bool operands as well as i32, because the PDF lists
  their dtype as "same" and only restricts `div`, `mod` and `shl` to i32. On bools they compute on 0 and 1 and
  normalize: `add` is or, `mul` is and, `max` is or, `cmplt false true` is true.

**Is this index safe?** `index [10 20 30] %i` with `%i` equal to 1 on this call gives 20. Whether the program is
valid depends on the bounds of `%i` across all calls: with `%i` in `[0, 2]` all three indices exist, and it's safe.
With `[0, 3]`, index 3 is past the end, so the program is rejected, whatever this call passes. The bounds rules are
deliberately simple: `mul %i %i` with `%i` in `[-1, 1]` is never negative, but its bounds are `[-1, 1]`.

**Same value, same cost?** With `%a = add 2 4` and `%b = add 3 3`, `mul %a %a` is 36 and costs 2 (one shared
add), while `mul %a %b` is also 36 but costs 3 (two distinct adds).

## 6. call and param

```
%x    = param [] [0 9] slot=0 dtype=i32 addrspace=ALU
%body = add %x 1
%r    = call %body 5
%t    = assert %r 6
```

* `call f a0 a1 ...` evaluates `f` with each param of slot `i` replaced by `ai`.
* **Bodies are closed.** Substitution doesn't go into the body (source 0) of a nested `call`. It does go into
  that call's arguments, which is how a body passes values inward:
  ```
  %p0    = param [] slot=0 dtype=i32 addrspace=ALU
  %inner = mul %p0 2          # inner's own slot 0
  %outer = call %inner %p0    # outer passes ITS slot 0 into inner's slot 0
  %r     = call %outer 5      # 10
  ```
* Each slot a body uses has exactly one param node: one dtype, one shape, one set of limits. Two different param
  nodes for one slot in one body are rejected. The same slot can mean different things in different bodies.
* Every used slot needs an argument, with the param's dtype, shape and address space. Unused and extra
  arguments are allowed.
* **Limits.** An argument's bounds must fit inside its param's limits `[l, h]`. A param with no limits is `I`
  (for bool, `[0, 1]`). The argument's bounds come from the rules above, so an outer param passed inward brings its
  own limits: `[0, 3]` fits in `[0, 5]`, `[0, 9]` does not.
* Week 1 arguments and returns are scalar values: the body and every argument is an i32 or a bool of shape `()`.
  `[]` is void, so it can't be an argument.
* A param only has a value inside a call. A param reachable from the assert without going through a call body is
  rejected.

## 7. Test files and outcomes

A test is a program that ends with a single `assert`, never used as an operand. "Single" counts assert bindings:
two `assert` lines are two asserts even if they're identical (and hash cons to one node). "Ends with" means the last
binding names the assert node: `%u = %t` after `%t = assert ...` is fine, anything else is not. Its left operand is the program's
return value, and in week 1 it is a scalar. Its right operand is a literal, or a stack of literals. Every node must
be reachable from the assertion, including call bodies and unused arguments.

The compiler checks a file in this order and stops at the first outcome:

1. **OVERBUDGET** if the file is over 4096 bytes. Nothing is parsed.
2. Parse. A file that doesn't follow sections 2 and 3 is **REJECTED**. Parsing covers the tokens and the
   grammar, names (undefined or defined twice), integer literals that don't fit, unknown ops, and attribute keys
   (a key the op doesn't take, or the same key twice). Attribute values, operand counts, dtypes and shapes are
   checked in step 4.
3. **OVERBUDGET** if parsing made 100 or more nodes, or 300 or more source edges. A node is a distinct (hash
   consed) node, literals and `[]` included. A source edge is one entry in one node's sources.
4. Validate: dtypes, shapes, index safety, call arguments, limits and the test-file rules. Any failure is
   **REJECTED**.
5. **OVERBUDGET** if the static cost is 1,000,000 or more.
6. Run it. **MATCH** if the values are equal, **MISMATCH** if they differ.

Nothing can go wrong at run time in week 1: every op is defined on every input, and an unsafe `index` never gets
past step 4.

**Static cost** is the sum, over the distinct nodes reachable from the assert, of each node's cost from section 5.
In week 1 every ALU result is a scalar, so N is 1 for them; a stack of n scalars costs n.
Each node counts once however many times it's used. Walk call arguments but not call bodies: a call charges its body
through `1 + C(f)`, where `C(f)` is the same sum over the body. Two different call nodes with the same body each
charge it. A body's sources include its params' sources, so a param's `[]` costs 1 inside the body, and limits like
`[0 9]` cost 2 more. For example, `%x = param [] slot=0 dtype=i32 addrspace=ALU`, `%s = add %x %x`,
`%v = call %s 3`, `%t = assert %v 6` costs 3: the call is 1, and its body is the add (1) plus the `[]` (1).

**Our readings:**
* The node and edge counts include every parsed node, reachable or not, because they're checked before
  validation.
* A file that is all comments has no bindings, so it's rejected (`file := binding+ EOF`).
* The left operand of the assert must be a scalar ("ALU returns must be scalar").

## 8. The command line

```
./compile [<file> ...]
```

Print one line per file to stdout: `<outcome> <file>`, with one space and the path exactly as it was given.

```
REJECTED tests/week1/rejected_assert_dtype_mismatch.uir
MATCH tests/week1/add_fold.uir
```

### Extra: `simplify FILE`

The PDF doesn't grade simplification, but the week 1 lectures cover it, and the course's simplify tests are good
practice for week 2 onward. `./compile simplify FILE` reads a program that defines `%out`, usually over params,
and has no assert. Print a valid .uir program that defines `%out` with the same dtype and shape and the same value
for every input inside the params' limits. The grader:

1. parses your output with the oracle
2. counts the **ops in your text**: every `%name = op ...` binding reachable from `%out`, except `param`. Atom
   bindings (`%x = 5`, `%y = %x`) and literals are free. Duplicate bindings count separately, so hash cons your
   output. The count must be at most the test's `max_ops`.
3. calls both versions on edge values in every param slot (the full cross product when there are 1 or 2 params),
   plus random values, all inside each param's limits. Results must match exactly.

Bugs this catches: `(x * 2) / 2 -> x` (it wraps), and `x mod 8 -> x` without limits that prove `x` is in `[0, 7]`.

## 9. Tests in this repo

A test's file name says what it expects: `mismatch_`, `rejected_` and `overbudget_` prefixes, MATCH otherwise.
The grader copies each test to a neutral name, `case.uir`, before your compiler sees it, so the name tells your
compiler nothing. Simplify tests start with a `# simplify: max_ops=N` comment.

```
python tools/test.py --compiler ./compile --week 1
python _reference/uirc.py --week=1 FILE...          # what the oracle prints for these files
```
