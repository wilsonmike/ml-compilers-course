int dot(const int *a, int sa, const int *b, int sb, int n) {
  int s = 0;
  for (int i = 0; i < n; i++) s += a[i * sa] * b[i * sb];
  return s;
}
