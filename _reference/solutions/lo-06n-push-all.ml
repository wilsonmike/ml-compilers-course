module Stack = struct
  type t = int list
  let empty = []
  let push x s = x :: s
  let pop s = match s with [] -> None | x :: rest -> Some (x, rest)
end

let push_all (xs : int list) (s : Stack.t) : Stack.t =
  List.fold_left (fun acc x -> Stack.push x acc) s xs
