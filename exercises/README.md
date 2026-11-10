# Lesson exercises

Each exercise is one JSON file here plus a reference solution in `_reference/solutions/<id>.<ml|c|uir>`.
`tools/serve.py` grades them. The browser only ever sees the starter code and the sample tests.

## In a lesson page

```html
<div class="exercise" data-ex="w0-c-sum-array">
  <h3>Sum an array with a pointer</h3>
  <p>The prompt: what to write, constraints, hints.</p>
</div>
<!-- a short "code quiz": same thing, stacked layout -->
<div class="exercise small" data-ex="w0-c-low-byte"> ... </div>
```

The page's prompt HTML stays in the page. The editor, examples, tests count, and results come from here.

## JSON

```json
{
  "id": "w0-c-sum-array",            // matches the file name; prefix w0- / w1-
  "lang": "c",                       // "c" | "ocaml" | "python" | "uir"
  "title": "Sum an array with a pointer",
  "starter": "int sum(const int *p, int n) {\n  return 0;\n}\n",
  "show": "%d",                      // c: printf format for each test value. ocaml: a printer expression, e.g. "string_of_int"
  "max_ops": 3,                      // uir only, optional: %out may use at most this many ops
  "tests": [
    {"expr": "({ int a[] = {1, 2, 3}; sum(a, 3); })", "expect": "6", "sample": true},
    {"expr": "sum(NULL, 0)", "expect": "0"}
  ]
}
```

* **c**: `expr` is a C expression (GNU statement expressions `({ ... })` are fine) printed with `show`.
  Each test runs in its own process, so a crash fails only that test. `<stdio.h> <stdlib.h> <stdint.h> <string.h> <math.h>` are included for you.
* **ocaml**: `expr` is an OCaml expression; the harness prints `show (expr)`. Exceptions are reported per test.
  Printers: `string_of_int`, `string_of_bool`, `Int32.to_string`, `(Printf.sprintf "%.9g")`, `(fun l -> String.concat " " (List.map string_of_int l))`.
* **python**: `expr` is a Python expression evaluated in the student's module, printed with `show`, a one-argument
  printer such as `str` or `lambda v: 'error' if v is None else str(v)`. Exceptions are reported per test. The code runs
  under the same Python as the course (3.10 or newer), isolated with `-I`.
* **uir**: the program must define `%out` over params. A test is `{"args": [5, -1], "expect": "4"}`;
  values print like the oracle (`-3`, `true`, `0.5`, `nan`, `[1 2 3]`).

## Language tracks

Learners write their compiler in Python (the default) or OCaml, picked in the sidebar. An exercise written for the
learner's own language has a Python version next to it: `<id>-py.json` (plus `_reference/solutions/<id>-py.py`), with a
`"prompt"` field, HTML that replaces the page's prompt for Python readers. The lesson page names both:

```html
<div class="exercise" data-ex="w1-02-div32" data-ex-py="w1-02-div32-py"> ... the OCaml prompt ... </div>
```

C and .uir exercises are the same in both tracks. In lesson text, `.only-python` and `.only-ocaml` (on any element)
show only on that track.

`expect` is compared to the printed value as trimmed text. Mark 1 to 3 tests `"sample": true`; they are shown and used by Run. Submit runs all of them. Aim for 5 to 10 tests, including edge cases (0, negatives, INT_MIN, empty input).

## Rules

* The starter must compile (so the student sees test failures, not a wall of errors) and must fail at least one test.
* The reference solution must pass every test. Prove both with:
  `python _reference/check_exercises.py --ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml"`
* OCaml exercises are drills, not pieces of the week's compiler handed over whole. The student writes their
  compiler in their own repo; exercises build the muscles (Int32 wrap, C division, pattern matching, a toposort on a toy type).
