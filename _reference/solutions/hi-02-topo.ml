let graph (pairs : (string * string list) list) : (string, string list) Hashtbl.t =
  let g = Hashtbl.create 16 in
  List.iter (fun (k, v) -> Hashtbl.replace g k v) pairs;
  g

let topo (g : (string, string list) Hashtbl.t) (root : string) : string list =
  let parts x = Option.value (Hashtbl.find_opt g x) ~default:[] in
  let started = Hashtbl.create 16 in
  let out = ref [] in
  let stack = ref [ (root, false) ] in
  while !stack <> [] do
    let x, ready = List.hd !stack in
    stack := List.tl !stack;
    if ready then out := x :: !out
    else if not (Hashtbl.mem started x) then begin
      Hashtbl.add started x ();
      stack := List.map (fun p -> (p, false)) (parts x) @ ((x, true) :: !stack)
    end
  done;
  List.rev !out
