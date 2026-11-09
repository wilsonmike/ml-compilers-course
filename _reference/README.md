# Spoilers: the reference compiler

This folder is a complete solution to every lab in the course. If you're taking the course, finish a week's lab
before you read the matching code here.

It's public on purpose. The course exists to help people learn, and copying this only shortchanges the person who
copies it. When you're stuck, the [debugging guide](../site/resources/debugging.html) and the hints in each lesson
come first. This is the last resort, and a good way to compare approaches once your own compiler passes.

You can use it without reading it. Run it to find out what a program should do:

```
python _reference/uirc.py run FILE        # the oracle: what should this program do?
python _reference/uirc.py simplify FILE   # one valid simplification (not the only one)
python _reference/uirc.py render FILE     # one valid C rendering (week 2 on)
```

| file | what |
|---|---|
| `uirc.py` | the reference compiler (the "oracle"): `python _reference/uirc.py run FILE`, `simplify FILE`, `render FILE` |
| `solutions/` | answers to the lesson exercises, the same ones the "Show answer" button reveals |
| `mutants.py` | plants 158 plausible bugs in `uirc.py`, one at a time, and checks that the test suite catches each one |
| `check_exercises.py` | checks every exercise: its solution passes and its starter code fails |

It's written in Python on purpose, so it can't be pasted into a compiler written in another language. Reading it
still gives the game away, so read it after you've tried.
