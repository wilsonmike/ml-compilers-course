let call_site (id : int) (n : int) (fields : string list) : string =
  Printf.sprintf "{ thread%d_ctx k_ = { %s }; uir_parallel_for(%d, thread%d, &k_); }"
    id (String.concat ", " fields) n id
