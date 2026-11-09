type op = Reshape of int list | Permute of int list | Pad of int list | Expand of int list | Reduce of int

let rec shape_after (shape : int list) (ops : op list) : int list =
  match ops with
  | [] -> shape
  | op :: rest ->
    let s = match op with
      | Reshape s | Expand s -> s
      | Permute order -> List.map (fun p -> List.nth shape p) order
      | Pad pads -> List.mapi (fun k d -> d + List.nth pads (2 * k) + List.nth pads (2 * k + 1)) shape
      | Reduce m -> List.filteri (fun i _ -> i >= m) shape
    in
    shape_after s rest
