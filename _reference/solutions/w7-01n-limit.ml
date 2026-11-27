let limit (peak : float) (bandwidth : float) (flops : float) (nbytes : float) : string =
  let intensity = flops /. nbytes in
  let memory_limit = bandwidth *. intensity in
  if memory_limit < peak then "memory" else "compute"
