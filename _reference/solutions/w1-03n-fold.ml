let wrap32 x = Int32.to_int (Int32.of_int x)

let floor_div a b =
  let q = a / b in
  if a mod b <> 0 && (a < 0) <> (b < 0) then q - 1 else q

let fold (op : string) (a : int) (b : int) : int =
  match op with
  | "add" -> wrap32 (a + b)
  | "mul" -> wrap32 (a * b)
  | "div" -> if b = 0 then -1 else wrap32 (floor_div a b)
  | _ -> 0
