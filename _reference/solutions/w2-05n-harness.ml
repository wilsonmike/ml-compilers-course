let print_line (slot : int) (i : int) : string =
  Printf.sprintf "printf(\"%d %%d\\n\", (int)b%d[%d]);" slot slot i

let harness (bufs : (int * int list) list) : string list =
  let decl (slot, data) =
    Printf.sprintf "static int32_t b%d[%d] = {%s};" slot (List.length data)
      (String.concat ", " (List.map string_of_int data)) in
  let names = List.map (fun (slot, _) -> Printf.sprintf "b%d" slot) bufs in
  let call = "kernel(" ^ String.concat ", " names ^ ");" in
  let prints = List.concat_map (fun (slot, data) -> List.mapi (fun i _ -> print_line slot i) data) bufs in
  List.map decl bufs @ [call] @ prints
