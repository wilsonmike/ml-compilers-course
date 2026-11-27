type node = { op : string; src : node list; arg : int option }

let lit v = { op = "const"; src = []; arg = Some v }
let node op a b = { op; src = [a; b]; arg = None }
let rec chain k = if k = 0 then lit 1 else let s = chain (k - 1) in node "add" s s

let count_boxes (root : node) : int =
  let seen = ref [] in
  let rec walk n =
    if List.memq n !seen then 0
    else begin
      seen := n :: !seen;
      List.fold_left (fun inside s -> inside + walk s) 1 n.src
    end
  in
  walk root
