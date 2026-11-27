let matmul (a : int array) (b : int array) (rows : int) (mid : int) (cols : int) : int array =
  let c = Array.make (rows * cols) 0 in
  for i = 0 to rows - 1 do
    for j = 0 to cols - 1 do
      let total = ref 0 in
      for k = 0 to mid - 1 do
        total := !total + a.(i * mid + k) * b.(k * cols + j)
      done;
      c.(i * cols + j) <- !total
    done
  done;
  c
