let shared (uses : int option list) : bool =
  match uses with
  | [] -> false
  | first :: rest -> first <> None && List.for_all (fun u -> u = first) rest
