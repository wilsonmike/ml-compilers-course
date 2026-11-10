(* Names the body uses but does not define (other than loop_var), sorted, no repeats.
   body: (name, uses) statements, in order. *)
let free_vars (body : (string * string list) list) (loop_var : string) : string list =
  let defined = List.map fst body in
  List.concat_map snd body
  |> List.filter (fun u -> not (List.mem u defined) && u <> loop_var)
  |> List.sort_uniq compare
