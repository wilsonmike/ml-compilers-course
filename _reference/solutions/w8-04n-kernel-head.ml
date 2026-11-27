let kernel_open (k : int) (counter : string) (params : (string * string) list) : string list =
  let ps = String.concat ", " (List.map (fun (ty, b) -> Printf.sprintf "%s *__restrict__ %s" ty b) params) in
  [Printf.sprintf "__global__ void k%d(%s) {" k ps;
   Printf.sprintf "  int32_t %s = blockIdx.x;" counter]

let launch (k : int) (blocks : int) (threads : int) (bufs : string list) : string =
  Printf.sprintf "UIR_LAUNCH(k%d, %d, %d, %s);" k blocks threads (String.concat ", " bufs)
