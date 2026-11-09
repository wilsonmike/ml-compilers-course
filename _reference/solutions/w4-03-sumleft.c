float sum_left(const float *x, int n) {
  float acc = x[0];
  for (int i = 1; i < n; i++) acc = acc + x[i];
  return acc;
}
