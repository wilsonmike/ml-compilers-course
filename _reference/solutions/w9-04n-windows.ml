let im2col (x : int array) (k : int) : int list list =
  List.init (Array.length x - k + 1) (fun i ->
    List.init k (fun j -> x.(i + j)))
