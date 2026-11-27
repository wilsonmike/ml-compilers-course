let greeting (argv : string array) : string =
  if Array.length argv = 2 then "hello, " ^ argv.(1)
  else "usage: " ^ argv.(0) ^ " NAME"
