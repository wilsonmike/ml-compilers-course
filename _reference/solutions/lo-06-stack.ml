module Stack = struct
  type t = int list
  let empty = []
  let push x s = x :: s
  let pop s = match s with [] -> None | x :: rest -> Some (x, rest)
  let peek s = match s with [] -> None | x :: _ -> Some x
end
