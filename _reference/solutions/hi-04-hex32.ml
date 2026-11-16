let hex32 (x : int) : string = Printf.sprintf "%08x" (x land 0xFFFFFFFF)
