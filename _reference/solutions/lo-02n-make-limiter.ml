let make_limiter top =
  fun x -> if x > top then top else x
