let int_min = -2147483648
let int_max = 2147483647

let wrap32 (n : int) : int =
  let m = n land 0xFFFFFFFF in
  if m >= 0x80000000 then m - 0x100000000 else m

let add32 (a : int) (b : int) : int = wrap32 (a + b)

let mul32 (a : int) (b : int) : int = wrap32 (a * b)

let div32 (a : int) (b : int) : int =
  if b = 0 then -1
  else
    let q = a / b in
    wrap32 (if a mod b <> 0 && (a < 0) <> (b < 0) then q - 1 else q)

let mod32 (a : int) (b : int) : int =
  if b = 0 then a
  else
    let r = a mod b in
    if r <> 0 && (r < 0) <> (b < 0) then r + b else r

let edges = [0; 1; -1; 1073741824; int_max; int_min]

let breaks (before : int -> 'a) (after : int -> 'a) : int list =
  List.filter (fun x -> before x <> after x) edges
