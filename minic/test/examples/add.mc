int add(int a, int b) { return a + b; }

int loop() {
      int x = -3;
      if (-x == 3) { x = x + 10; } else { x = 0; }
      return x;
    }

int main() {
  int x = 2;
  int y = loop(x);
  int z = add(x, y);

  return z;        // 进程退出码应为 5
}
