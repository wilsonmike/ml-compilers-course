let skeleton (loops : (string * string) list) (body : string) : string =
  let n = List.length loops in
  let pad d = String.make (2 * d) ' ' in
  let opens = List.mapi (fun d (v, b) -> Printf.sprintf "%sfor (int32_t %s = 0; %s < %s; %s++) {" (pad d) v v b v) loops in
  let closes = List.init n (fun d -> pad (n - 1 - d) ^ "}") in
  String.concat "\n" (opens @ [pad n ^ body] @ closes)
