type item =
  | Store of int
  | Reduce of int
  | Stage of int
  | Expand of int
  | Scalar

let trips (prog : item list) : int list =
  List.concat_map
    (function
      | Store n | Stage n -> [n]
      | Reduce n -> [n - 1]
      | Expand _ | Scalar -> [])
    prog
