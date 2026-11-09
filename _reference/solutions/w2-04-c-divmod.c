int32_t c_div(int32_t a, int32_t b) {
  return b == -1 ? (int32_t)(0u - (uint32_t)a) : a / b;
}

int32_t c_mod(int32_t a, int32_t b) {
  return b == -1 ? 0 : a % b;
}
