long long gemm_flops(int M, int N, int K) {
  return 2LL * M * N * K;   // widen before multiplying, or 2048^3 overflows int
}
