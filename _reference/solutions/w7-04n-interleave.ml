let run (schedule : int list) : int =
  let counter = ref 0 in
  let reg = [| 0; 0 |] in
  let step = [| 0; 0 |] in
  List.iter (fun t ->
    (match step.(t) mod 3 with
     | 0 -> reg.(t) <- !counter
     | 1 -> reg.(t) <- reg.(t) + 1
     | _ -> counter := reg.(t));
    step.(t) <- step.(t) + 1) schedule;
  !counter
