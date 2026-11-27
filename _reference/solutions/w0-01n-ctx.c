#include <stdint.h>

typedef struct { int32_t *b0; int32_t r3; } ctx_t;

void body(int32_t r, void *ctx) {
  ctx_t *k = ctx;
  k->b0[r] = k->r3 + r;
}

void run(int32_t n, void (*f)(int32_t, void *), void *ctx) {
  for (int32_t r = 0; r < n; r++) {
    f(r, ctx);
  }
}
