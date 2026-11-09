void normalize(const float *x, float *y, int n) {
  float s = x[0];
  for (int i = 1; i < n; i++) s = s + x[i];
  float r = 1.0f / s;
  for (int i = 0; i < n; i++) y[i] = x[i] * r;
}
