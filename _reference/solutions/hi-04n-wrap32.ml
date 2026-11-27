let wrap32 (x : int) : int =
  let count = x land 0xFFFFFFFF in
  if count >= 2147483648 then count - 4294967296 else count
