(* phases: the C statements of each local loop; names: the variable each one uses.
   The CUDA body: each phase as { int32_t name = threadIdx.x; ...statements } then __syncthreads(); *)
let fuse_phases (phases : string list list) (names : string list) : string list =
  List.concat (List.map2 (fun stmts n ->
    ["{"; Printf.sprintf "  int32_t %s = threadIdx.x;" n] @ List.map (fun s -> "  " ^ s) stmts @ ["}"; "__syncthreads();"]) phases names)
