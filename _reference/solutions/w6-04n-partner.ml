let shrink_offsets (pads : int list) : int list =
  List.filteri (fun i _ -> i mod 2 = 0) pads

let pad_widths (offsets : int list) (sizes : int list) (dims : int list) : int list =
  List.concat (List.map2 (fun o (s, d) -> [o; d - o - s]) offsets (List.combine sizes dims))
