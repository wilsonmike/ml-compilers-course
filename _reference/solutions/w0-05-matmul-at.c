void matmul_at(int M, int N, int K, const int *At, const int *B, int *C) {
  for (int i = 0; i < M; i++)
    for (int j = 0; j < N; j++) {
      int acc = 0;
      for (int k = 0; k < K; k++) acc += At[k * M + i] * B[k * N + j];
      C[i * N + j] = acc;
    }
}
