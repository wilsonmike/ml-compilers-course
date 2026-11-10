# ML compilers, from zero

A free, open-source course where you build a machine learning compiler from scratch, inspired by the public syllabus
of [10-411, Compilers for Machine Learning](https://10-411.com/)
([technical syllabus](https://gist.github.com/geohot/4768597d9dc536446ee2d5de1f29e89d)).
**Independent. Not affiliated with CMU or George Hotz.**

The original course assumes strong C, a systems course, and some GPU experience. This one adds a week 0 that teaches
those, and puts a diagram before every idea.

## Status: weeks 0 to 5

| week | topic | lessons | tests | spec |
|---|---|---|---|---|
| 0 | prerequisites: C, memory, IRs, tensors, matmul, OCaml | 6 | exercises only | |
| 1 | UOps and rewrites | 6 | 142 | [uir-week1.md](spec/uir-week1.md) |
| 2 | memory and rendering C | 6 | 99 | [uir-week2.md](spec/uir-week2.md) |
| 3 | loops | 6 | 89 | [uir-week3.md](spec/uir-week3.md) |
| 4 | rangeify, reduce, materialization | 6 | 77 | [uir-week4.md](spec/uir-week4.md) |
| 5 | movement ops: reshape, permute, pad, shrink, any rank | 6 | 94 | [uir-week5.md](spec/uir-week5.md) |

221 quizzes with hints and answers, 84 graded exercises, and 501 compiler tests. The tests catch all 158 bugs that
`_reference/mutants.py` plants in the reference compiler. The `.uir` format is our own until the official 10-411 one
is published, and then the specs and tests migrate.

## Taking the course

```
git clone https://github.com/wilsonmike/ml-compilers-course
cd ml-compilers-course
python tools/serve.py                       # the course and exercise runner at http://127.0.0.1:4111
```

Python 3.10 or newer, standard library only. Every lesson has LeetCode-style exercises in OCaml, C, or .uir. Type in
the editor (Vim, Emacs, or Sublime keys, picked in the sidebar). **Run** checks the examples and **Submit** runs the
hidden tests, compiled on your machine. C needs `clang` or `gcc`, and OCaml needs `ocaml` on PATH. Without a local
OCaml you can use `--ocaml "docker run --rm -i ocaml/opam:alpine-ocaml-5.2 ocaml"`. The runner only listens on
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
| `tools/design_lint.py` | checks the site against the design and copy rules |
| `site/vendor/codemirror/` | CodeMirror 5.65.16 (MIT), vendored so nothing loads from a CDN |
| `_reference/` | **spoilers.** The reference compiler, the exercise answers, and the mutation harness. |

## How the suite is proven

```
python tools/test.py --self-check --week 1      # every test header agrees with the reference compiler
python _reference/mutants.py                    # every planted bug fails at least one test
python _reference/check_exercises.py            # every exercise: the solution passes and the starter fails
```

1. `--self-check`: every test header agrees with the reference, and the reference reaches every simplify target.
2. The tricky values (f32 rounding, i32 wrap, C division, f32 to i32 casts) were cross-checked against real C compiled
   with clang.
3. `_reference/mutants.py` plants 158 plausible bugs into the reference, one at a time. Each must fail at least one
   test, and an unmutated control copy must pass all of them.

## Contributing

Fixes to lessons, tests, and specs are welcome. Before a pull request, run the checks above for the weeks you touched,
`python tools/design_lint.py`, and `python tools/build_static.py` if you changed an exercise.

## License

Code is MIT ([`LICENSE`](LICENSE)). The lessons and specs are CC BY-NC-SA 4.0. See
[`LICENSE-CONTENT.md`](LICENSE-CONTENT.md) for which is which.
