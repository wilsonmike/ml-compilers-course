let stage_set (g : (int * int list) list) : int list =
  let count = Hashtbl.create 16 in
  List.iter (fun (_, srcs) ->
    List.iter (fun s -> Hashtbl.replace count s (1 + (try Hashtbl.find count s with Not_found -> 0)))
      (List.sort_uniq compare srcs)) g;
  g |> List.filter (fun (id, srcs) -> srcs <> [] && (try Hashtbl.find count id with Not_found -> 0) >= 2)
    |> List.map fst |> List.sort compare
