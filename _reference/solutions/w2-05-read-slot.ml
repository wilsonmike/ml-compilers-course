let read_slot (out : string) (k : int) : float list =
  String.split_on_char '\n' out
  |> List.filter_map (fun line ->
       match String.split_on_char ' ' (String.trim line) with
       | [s; bits] when int_of_string s = k -> Some (Int32.float_of_bits (Int32.of_string ("0x" ^ bits)))
       | _ -> None)
