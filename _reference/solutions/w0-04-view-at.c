int view_at(int ndim, const int *shape, const int *strides, int offset, int k) {
  int at = offset;
  for (int d = ndim - 1; d >= 0; d--) {   // unravel k from the last (fastest) axis
    at += (k % shape[d]) * strides[d];
    k /= shape[d];
  }
  return at;
}
