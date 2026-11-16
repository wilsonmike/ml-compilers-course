module StringMap = Map.Make (String)

let count_words (words : string list) : int StringMap.t =
  List.fold_left
    (fun m w ->
      let n = match StringMap.find_opt w m with Some n -> n | None -> 0 in
      StringMap.add w (n + 1) m)
    StringMap.empty words
