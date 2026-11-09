type node = { name : string; srcs : string list }

let topo (graph : node list) (root : string) : string list =
  let seen = Hashtbl.create 16 and out = ref [] in
  let rec go n =
    if not (Hashtbl.mem seen n) then begin
      Hashtbl.add seen n ();
      List.iter go (List.find (fun x -> x.name = n) graph).srcs;
      out := n :: !out
    end in
  go root; List.rev !out
