let dot (a : float array) (b : float array) : float =
  let total = ref 0.0 in
  for k = 0 to Array.length a - 1 do
    total := !total +. a.(k) *. b.(k)
  done;
  !total

let dot_blocks (a : float array) (b : float array) (block : int) : float =
  let n = Array.length a in
  let total = ref 0.0 in
  let start = ref 0 in
  while !start < n do
    for k = !start to min (!start + block) n - 1 do
      total := !total +. a.(k) *. b.(k)
    done;
    start := !start + block
  done;
  !total
