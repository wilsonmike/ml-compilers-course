int fits(int n, int per_elem, int fixed) {
  return (long long)n * per_elem + fixed <= 20000;
}
