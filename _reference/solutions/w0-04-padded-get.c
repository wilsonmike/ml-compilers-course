int padded_get(const int *row, int n, int left, int j) {
  int i = j - left;
  return (0 <= i && i < n) ? row[i] : 0;   // the mask: invalid positions never touch memory
}
