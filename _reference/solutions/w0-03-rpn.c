int rpn(const char *s) {
  int st[64], n = 0;
  for (; *s; s++) {
    if (*s >= '0' && *s <= '9') { st[n++] = *s - '0'; continue; }
    int b = st[--n], a = st[--n];
    st[n++] = *s == '+' ? a + b : *s == '-' ? a - b : a * b;
  }
  return st[0];
}
