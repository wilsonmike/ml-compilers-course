let ordered (stores : (string * string) list) (afters : (string * string * string) list) : bool =
  let versions = List.map snd stores in
  let one_per_version =
    List.length (List.sort_uniq compare versions) = List.length versions in
  let sequenced (name, version) =
    List.filter_map (fun (_, m, s) -> if s = name then Some m else None) afters = [version] in
  one_per_version && List.for_all sequenced stores
