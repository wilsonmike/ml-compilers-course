int coord(int f, int d1, int d2, int axis) {
  if (axis == 0) return f / (d1 * d2);
  if (axis == 1) return f / d2 % d1;
  return f % d2;
}
