let launch (blocks : int) (size : int) (x : int array) : int array =
  let out = Array.make (Array.length x) 0 in
  for b = 0 to blocks - 1 do
    for t = 0 to size - 1 do
      let i = size * b + t in
      out.(i) <- x.(i) * 2
    done
  done;
  out
