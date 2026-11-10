# ML compilers, from zero

A free, open-source course where you build a machine learning compiler from scratch, inspired by the public syllabus
of [10-411, Compilers for Machine Learning](https://10-411.com/)
([technical syllabus](https://gist.github.com/geohot/4768597d9dc536446ee2d5de1f29e89d)).
**Independent. Not affiliated with CMU or George Hotz.**

The original course assumes strong C, a systems course, and some GPU experience. This one adds a week 0 that teaches
those, and puts a diagram before every idea.

## Status: weeks 0 to 7

| week | topic | lessons | tests | spec |
|---|---|---|---|---|
| 0 | prerequisites: C, memory, IRs, tensors, matmul, Python or OCaml | 7 | exercises only | |
| 1 | UOps and rewrites | 6 | 148 | [uir-week1.md](spec/uir-week1.md) |
| 2 | memory and rendering C | 6 | 100 | [uir-week2.md](spec/uir-week2.md) |
| 3 | loops | 6 | 90 | [uir-week3.md](spec/uir-week3.md) |
| 4 | rangeify, reduce, materialization | 6 | 78 | [uir-week4.md](spec/uir-week4.md) |
| 5 | movement ops: reshape, permute, pad, shrink, any rank | 6 | 96 | [uir-week5.md](spec/uir-week5.md) |
| 6 | math ops, sugar, autodiff, data files, training on MNIST | 6 | 147 | [uir-week6.md](spec/uir-week6.md) |
| 7 | fast kernels: tiling, upcast, threads, speed tests | 6 | 41 | [uir-week7.md](spec/uir-week7.md) |

287 quizzes with hints and answers, 132 graded exercises (33 of them in Python), and 700 compiler tests. The tests catch all 216 plausible bugs that `_reference/mutants.py` plants in the
reference compiler, one at a time. `--checks` also switches off each of its 146 validations and simplifier rules:
113 are caught, and the other 33 are backed up by a second check that rejects the same program. The `.uir` format is our own until the official 10-411 one
is published, and then the specs and tests migrate.

## Taking the course

```
git clone https://github.com/wilsonmike/ml-compilers-course
cd ml-compilers-course
python tools/serve.py                       # the course and exercise runner at http://127.0.0.1:4111
```

Python 3.10 or newer, standard library only.

You write your compiler in one of two languages, picked under Language in the sidebar: **Python** (the default) or
**OCaml**. Lesson 0.7 sets up a Python compiler project and covers the Python traps that matter here (i32 wrapping,
floor division, f32 rounding). Lesson 0.6 teaches OCaml from scratch. Exercises and the few instructions that differ
follow the track you pick.

Every lesson has LeetCode-style exercises in your language, C, or .uir. Type in the editor (Vim, Emacs, or Sublime
keys, picked in the sidebar). **Run** checks the examples and **Submit** runs the hidden tests, on your machine.
Python exercises need nothing extra. C needs `clang` or `gcc`, and OCaml exercises need `ocaml` on PATH. Without a
local OCaml you can use `--ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml"`. The runner only listens on
127.0.0.1 and refuses requests from other sites.

The lessons also read fine on the hosted site or straight from disk. There the exercises show their examples, hints,
and answers, and running code needs the local runner.

## Grading your compiler

Write your compiler in any language, in its own repository. `templates/AGENTS.md` is a starting point if you use an
AI assistant and want it to explain rather than write your code.

```
python tools/test.py --compiler C:/path/to/your.exe --week 1        # grade your compiler
python tools/test.py --compiler C:/path/to/your.exe -k call -v      # one topic, with details
python tools/test.py --check-tests C:/path/to/your/tests/week1      # check your own tests' headers
```

`--compiler` is anything the runner can start as `COMPILER run FILE`: a built OCaml executable such as
`_build/default/bin/main.exe`, or for a Python compiler the small wrapper script from lesson 0.7 (`mlc.cmd` on Windows,
an executable `mlc` script on macOS and Linux).

## Layout

| path | what |
|---|---|
| `site/` | the lessons, quizzes, and study resources. No build step, no dependencies. |
| `spec/` | the .uir format and semantics for each week |
| `tests/weekN/` | the compiler tests: `run` tests with a `# expect:` header, `simplify` tests with a `# simplify:` header, and `render` tests from week 2 |
| `exercises/` | lesson exercises: starter code and tests (see `exercises/README.md`) |
| `tools/test.py` | the compiler test runner |
| `tools/serve.py` | the local course server and exercise runner |
| `tools/build_helpers.py`, `tools/build_static.py` | generate the test guides and the exercise data for the hosted site |
| `tools/check.py` | every check, in one command (below) |
| `site/vendor/codemirror/` | CodeMirror 5.65.16 (MIT), vendored so nothing loads from a CDN |
| `_reference/` | **spoilers.** The reference compiler, the exercise answers, and the mutation harness. |

## Checking a change

```
python tools/check.py           # about a minute: everything below except the two slow ones, in parallel
python tools/check.py --full    # also the MNIST training test and the planted-bug run (about 6 minutes)
```

What it runs, and what each part protects:

| check | catches |
|---|---|
| `tools/design_lint.py` | design and copy rules: tints, small text, em dashes, semicolons in prose |
| `tools/check_site.py` | broken HTML, quiz keys that aren't an option, quizzes missing a hint or explanation, broken links, exercises without a solution, inline scripts that don't parse |
| `tools/check_spec_w6.py` | the week 6 spec's math definitions drifting from the reference |
| `tools/test.py --self-check --week N` | a test header that disagrees with the reference compiler |
| `_reference/check_exercises.py` | an exercise whose solution fails or whose starter already passes |
| `_reference/mutants.py` | tests too weak to notice a bug: it plants 216 plausible bugs into the reference, one at a time, and each must fail some test while an unmutated copy passes them all (5 minutes). `--checks` adds one bug per validation and simplifier rule. `--matrix` records every test each bug fails, for the test guides. |

The tricky values (f32 rounding, i32 wrap, C division, f32 to i32 casts) were also cross-checked against real C
compiled with clang, and the week 6 gradients against finite differences.

## Contributing

Fixes to lessons, tests, and specs are welcome. Run `python tools/check.py` before a pull request, and
`python tools/build_seo.py` if you added or renamed a page.

## License

Code is MIT ([`LICENSE`](LICENSE)). The lessons and specs are CC BY-NC-SA 4.0. See
[`LICENSE-CONTENT.md`](LICENSE-CONTENT.md) for which is which.
