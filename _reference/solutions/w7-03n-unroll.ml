let unroll (n : int) (body : string list) : string list =
  List.concat (List.init n (fun r ->
    List.map (fun line -> String.concat (string_of_int r) (String.split_on_char '@' line)) body))
