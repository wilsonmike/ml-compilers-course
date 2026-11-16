let join (sep : string) (parts : string list) : string =
  let b = Buffer.create 16 in
  List.iteri
    (fun i p ->
      if i > 0 then Buffer.add_string b sep;
      Buffer.add_string b p)
    parts;
  Buffer.contents b
