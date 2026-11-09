void conv2d(const int *x, int H, int W, const int *k, int KH, int KW, int *y) {
  int OH = H - KH + 1, OW = W - KW + 1;
  for (int oi = 0; oi < OH; oi++)
    for (int oj = 0; oj < OW; oj++) {
      int acc = 0;
      for (int ki = 0; ki < KH; ki++)
        for (int kj = 0; kj < KW; kj++)
          acc += x[(oi + ki) * W + (oj + kj)] * k[ki * KW + kj];
      y[oi * OW + oj] = acc;
    }
}
