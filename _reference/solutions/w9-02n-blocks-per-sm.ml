let blocks_per_sm (threads : int) (regs : int) (shared_kb : int) : int =
  if threads > 1024 || regs > 255 || shared_kb > 48 then 0
  else min (65536 / (threads * regs)) (min (1536 / threads) (100 / shared_kb))
