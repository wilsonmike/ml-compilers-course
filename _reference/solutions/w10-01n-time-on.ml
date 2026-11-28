let time_on (n : int) (work : int) (mb : int) (speed : int) : int =
  if n = 1 then work
  else work / n + mb / speed
