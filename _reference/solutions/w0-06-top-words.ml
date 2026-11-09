let top_words (k : int) (words : string list) : (string * int) list =
  let t = Hashtbl.create 64 in
  List.iter (fun w -> Hashtbl.replace t w (1 + Option.value ~default:0 (Hashtbl.find_opt t w))) words;
  let all = Hashtbl.fold (fun w n acc -> (w, n) :: acc) t [] in
  let sorted = List.sort (fun (a, n) (b, m) -> if n <> m then compare m n else compare a b) all in
  List.filteri (fun i _ -> i < k) sorted
