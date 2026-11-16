let safe_div (a : int) (b : int) : (int, string) result =
  if b = 0 then Error "division by zero" else Ok (a / b)
