type mov =
  | Permute of int list
  | Expand of int list
  | Shrink of int list

let rec position (a : int) (order : int list) : int =
  match order with
  | [] -> failwith "not a permutation"
  | p :: rest -> if p = a then 0 else 1 + position a rest

let src (op : mov) (idx : int list) : int list =
  match op with
  | Permute order -> List.mapi (fun a _ -> List.nth idx (position a order)) order
  | Expand shape -> List.map2 (fun s i -> if s = 1 then 0 else i) shape idx
  | Shrink offsets -> List.map2 (fun i o -> i + o) idx offsets
