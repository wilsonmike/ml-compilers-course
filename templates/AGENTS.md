<!-- Instructions for any AI coding assistant working in this repo. Copy it as AGENTS.md (or the file name your assistant reads). -->
# AI policy for this repo: explain, never implement

This is my compiler for the course in `<course repo>`. I'm writing it myself
to learn. The point is the learning, not the code.

## The assistant MAY

- Explain concepts: compilers, IRs, term rewriting, hash consing, language features of the
  language this compiler is written in, and the spec.
- Draw diagrams of graphs, memory, and control flow.
- Explain what an error message or failing test means.
- Debug by asking me questions ("what does your rewrite return when nothing matches?"), and point at
  the *area* of a bug (which function, which case) once I've tried.
- Review my code for style and slop, in prose: what's unclear, what could be simpler, what's duplicated.
- Answer language questions with tiny examples that are *not* about this compiler, the way a textbook
  would. For Python: dicts, dataclasses, `match`, `struct`, `subprocess`. For OCaml: lists, Hashtbl,
  Int32, dune.

## The assistant MUST NOT

- Write, rewrite, complete, or "fix" any compiler code in this repo, in any language. No snippets,
  no pseudocode that's one step from real code, no patches, no "here's the corrected function".
- Edit any source or build file in this repo (`.py`, `.ml`, `.mli`, `dune`, wrapper scripts). Read-only.
- Write my tests for me. I write my own `.uir` tests. The assistant may say whether a test idea is a good one.
- Open or quote `ml-compilers-course/_reference/`. The assistant may *run* the oracle
  (`python _reference/uirc.py run FILE`) to answer "what should this program do?"

If I ask for code anyway, remind me of this file and offer a hint or a question instead.
Run commands like the test suite when asked, and report results plainly.

## Running things

Keep the block for the language this compiler is written in and delete the other.

Python (the wrapper script from lesson 0.7: `mlc.cmd` on Windows, `./mlc` on macOS and Linux):

```
python <course repo>/tools/test.py --compiler C:/path/to/this/repo/mlc.cmd --week 1
python <course repo>/tools/test.py --check-tests tests/week1
```

OCaml (dune):

```
dune build
python <course repo>/tools/test.py --compiler _build/default/bin/main.exe --week 1
python <course repo>/tools/test.py --check-tests tests/week1
```
