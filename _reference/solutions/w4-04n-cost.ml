let fuse_cost (ops : int) (uses : int) (n : int) : int =
  ops * uses * n

let stage_cost (ops : int) (uses : int) (n : int) (mem : int) : int =
  ops * n + mem * n + mem * uses * n

let choose (ops : int) (uses : int) (n : int) (mem : int) : string =
  if stage_cost ops uses n mem < fuse_cost ops uses n then "stage" else "fuse"
