int pad_src(int i, int l, int n) {
  int j = i - l;
  if (j < 0) j = 0;
  if (j > n - 1) j = n - 1;
  return j;
}

int pad_valid(int i, int l, int n) {
  return i >= l && i < l + n;
}
