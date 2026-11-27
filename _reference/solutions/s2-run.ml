type arg = Lit of int | Name of string

let apply (op : string) (a : int) (b : int) : int =
  match op with
  | "add" -> a + b
  | "mul" -> a * b
  | "max" -> max a b
  | _ -> failwith op

let run (prog : (string * string * arg * arg) list) : int =
  let env = Hashtbl.create 16 in
  let value = function Lit n -> n | Name s -> Hashtbl.find env s in
  let last = ref 0 in
  List.iter (fun (name, op, x, y) ->
    let a = value x in
    let b = value y in
    let v = apply op a b in
    Hashtbl.replace env name v;
    last := v) prog;
  !last
