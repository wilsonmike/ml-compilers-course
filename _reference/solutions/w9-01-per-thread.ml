(* accesses: (s, lo, hi, size) each, s = None when t isn't a plain multiple in the offset.
   The shared s when every access stays in its thread's slice, else 0. *)
let per_thread (accesses : (int option * int * int * int) list) : int =
  match accesses with
  | (Some s, _, _, _) :: _ when s > 0 ->
    if List.for_all (fun (s2, lo, hi, size) -> s2 = Some s && lo >= 0 && hi + size <= s) accesses then s else 0
  | _ -> 0
