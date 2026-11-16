type shape = Circle of float | Rect of float * float | Square of float

let perimeter (s : shape) : float =
  match s with
  | Circle r -> 2.0 *. Float.pi *. r
  | Rect (w, h) -> 2.0 *. (w +. h)
  | Square a -> 4.0 *. a
