long long lines_touched(long long start, int n) {
  if (n == 0) return 0;
  long long last = start + 4LL * n - 1;
  return last / 64 - start / 64 + 1;
}
