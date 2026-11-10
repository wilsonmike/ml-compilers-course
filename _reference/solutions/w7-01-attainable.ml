(* Best reachable GFLOP/s: limited by compute (peak, GFLOP/s) and by memory (bandwidth, GB/s). *)
let attainable (peak : float) (bandwidth : float) (flops : float) (nbytes : float) : float =
  Float.min peak (bandwidth *. flops /. nbytes)
