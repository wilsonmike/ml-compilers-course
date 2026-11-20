int32_t uir_div(int32_t a, int32_t b) {
  if (b == 0) return -1;
  if (b == -1) return (int32_t)(0u - (uint32_t)a);
  int32_t q = a / b;
  return (q * b != a && (a < 0) != (b < 0)) ? q - 1 : q;
}

int32_t uir_mod(int32_t a, int32_t b) {
  if (b == 0) return a;
  if (b == -1) return 0;
  int32_t r = a % b;
  return (r != 0 && (r < 0) != (b < 0)) ? r + b : r;
}
