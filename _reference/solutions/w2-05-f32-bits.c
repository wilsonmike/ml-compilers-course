uint32_t f32_bits(float x) {
  uint32_t u;
  memcpy(&u, &x, sizeof u);
  return u;
}
