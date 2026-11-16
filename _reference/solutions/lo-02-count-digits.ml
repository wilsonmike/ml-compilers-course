let rec count_digits n =
  if n < 10 then 1 else 1 + count_digits (n / 10)
