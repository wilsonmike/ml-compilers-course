let matmul_tiled (a : float array array) (b : float array array) (th : int) (tw : int) : float array array =
  let n = Array.length a and p = Array.length b and m = Array.length b.(0) in
  let c = Array.make_matrix n m 0.0 in
  for ib = 0 to n / th - 1 do
    for jb = 0 to m / tw - 1 do
      for k = 0 to p - 1 do
        for i = ib * th to ib * th + th - 1 do
          for j = jb * tw to jb * tw + tw - 1 do
            c.(i).(j) <- c.(i).(j) +. a.(i).(k) *. b.(k).(j)
          done
        done
      done
    done
  done;
  c
