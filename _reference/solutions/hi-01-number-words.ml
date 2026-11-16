let number_words (words : string list) : int list =
  let table = Hashtbl.create 16 in
  List.map
    (fun w ->
      match Hashtbl.find_opt table w with
      | Some n -> n
      | None ->
        let n = Hashtbl.length table in
        Hashtbl.add table w n;
        n)
    words
