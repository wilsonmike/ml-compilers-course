int32_t uir_add(int32_t a, int32_t b) {
  return (int32_t)((uint32_t)a + (uint32_t)b);
}

int32_t uir_mul(int32_t a, int32_t b) {
  return (int32_t)((uint32_t)a * (uint32_t)b);
}

int32_t uir_shl(int32_t a, int32_t b) {
  return (int32_t)((uint32_t)a << ((uint32_t)b & 31u));
}
