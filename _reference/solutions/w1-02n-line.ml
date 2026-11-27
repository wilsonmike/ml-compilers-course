type arg = Lit of int | Name of string

let atom (word : string) : arg =
  if word.[0] = '%' then Name (String.sub word 1 (String.length word - 1))
  else Lit (int_of_string word)

let parse_line (line : string) : string * string * arg * arg =
  let words = List.filter (fun w -> w <> "") (String.split_on_char ' ' line) in
  match words with
  | [def; _; op; x; y] ->
    let name = String.sub def 1 (String.length def - 1) in
    let a = atom x in
    let b = atom y in
    (name, op, a, b)
  | _ -> failwith "not a line"
