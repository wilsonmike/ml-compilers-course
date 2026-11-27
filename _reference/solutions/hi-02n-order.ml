let graph (pairs : (string * string list) list) : (string, string list) Hashtbl.t =
  let g = Hashtbl.create 16 in
  List.iter (fun (k, v) -> Hashtbl.replace g k v) pairs;
  g

let cooking_order (g : (string, string list) Hashtbl.t) (dish : string) : string list =
  let parts x = Option.value (Hashtbl.find_opt g x) ~default:[] in
  let done_ = Hashtbl.create 16 in
  let order = ref [] in
  let rec visit item =
    if not (Hashtbl.mem done_ item) then begin
      Hashtbl.replace done_ item ();
      List.iter visit (parts item);
      order := item :: !order
    end
  in
  visit dish;
  List.rev !order
