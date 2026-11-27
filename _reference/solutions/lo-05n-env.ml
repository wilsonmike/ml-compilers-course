let final_value (lines : (string * int) list) (name : string) : int =
  let env = Hashtbl.create 16 in
  List.iter (fun (k, v) -> Hashtbl.replace env k v) lines;
  match Hashtbl.find_opt env name with
  | Some v -> v
  | None -> 0
