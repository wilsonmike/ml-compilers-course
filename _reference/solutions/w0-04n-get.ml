let get (grid : int list) (rows : int) (cols : int) (r : int) (c : int) : int =
  List.nth grid (r * cols + c)
