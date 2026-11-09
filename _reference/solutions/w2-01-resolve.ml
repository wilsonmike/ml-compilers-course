type view =
  | Buffer of int                (* a whole buffer of n elements *)
  | Shrink of view * int * int   (* parent, offset, k elements:  shrink p off shape=[k] *)
  | Elem of view * int           (* parent, offset, one element: shrink p off shape=[] *)

let rec resolve (v : view) : int * int =
  let step p off k =
    let (s, len) = resolve p in
    if off < 0 || off + k > len then raise (Invalid_argument "out of bounds");
    (s + off, k) in
  match v with
  | Buffer n -> (0, n)
  | Shrink (p, off, k) -> step p off k
  | Elem (p, off) -> step p off 1
