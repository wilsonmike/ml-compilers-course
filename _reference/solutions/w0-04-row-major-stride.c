int row_major_stride(int ndim, const int *shape, int d) {
  int s = 1;
  for (int i = d + 1; i < ndim; i++) s *= shape[i];
  return s;
}
