let word_counts (words : string list) : (string * int) list =
  let t = Hashtbl.create 16 in
  List.iter
    (fun w ->
      let n = match Hashtbl.find_opt t w with Some n -> n | None -> 0 in
      Hashtbl.replace t w (n + 1))
    words;
  List.sort compare (Hashtbl.fold (fun w n acc -> (w, n) :: acc) t [])
