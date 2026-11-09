void transpose(const int *src, int *dst, int rows, int cols) {
  for (int i = 0; i < rows; i++)
    for (int j = 0; j < cols; j++)
      dst[j * rows + i] = src[i * cols + j];
}
