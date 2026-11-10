(* Little-endian 32-bit two's complement integers, back to back. *)
let decode_i32 (data : string) : int list =
  if String.length data mod 4 <> 0 then failwith "not a whole number of i32";
  List.init (String.length data / 4) (fun k ->
    let b j = Char.code data.[4 * k + j] in
    let u = b 0 lor (b 1 lsl 8) lor (b 2 lsl 16) lor (b 3 lsl 24) in
    if u >= 1 lsl 31 then u - (1 lsl 32) else u)
