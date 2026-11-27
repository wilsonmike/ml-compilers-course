type facts = {
  size : int; parses : bool; nodes : int; edges : int;
  valid : bool; cost : int; got : int; want : int;
}

let outcome (f : facts) : string =
  if f.size > 4096 then "OVERBUDGET"
  else if not f.parses then "REJECTED"
  else if f.nodes >= 100 || f.edges >= 300 then "OVERBUDGET"
  else if not f.valid then "REJECTED"
  else if f.cost >= 1000000 then "OVERBUDGET"
  else if f.got = f.want then "MATCH"
  else "MISMATCH"
