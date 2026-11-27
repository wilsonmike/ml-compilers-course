let ops = ["add"; "mul"; "max"]

let known_op (name : string) : bool =
  List.exists (fun op -> op = name) ops
