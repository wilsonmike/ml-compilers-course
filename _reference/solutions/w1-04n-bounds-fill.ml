type range = { lo : int; hi : int }

let const_range (v : int) : range = { lo = v; hi = v }

let max_range (a : range) (b : range) : range =
  { lo = max a.lo b.lo; hi = max a.hi b.hi }

let cmplt_range (a : range) (b : range) : range =
  if a.hi < b.lo then { lo = 1; hi = 1 }
  else if a.lo >= b.hi then { lo = 0; hi = 0 }
  else { lo = 0; hi = 1 }
