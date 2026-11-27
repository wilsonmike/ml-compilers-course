let matvec (m : int array) (rows : int) (cols : int) (v : int array) : int array =
  let out = Array.make rows 0 in
  for r = 0 to rows - 1 do
    for c = 0 to cols - 1 do
      out.(r) <- out.(r) + m.(r * cols + c) * v.(c)
    done
  done;
  out
