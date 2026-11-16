// Example 7: Function Definition and Calling
// Demonstrates parameter pushing (param), call instruction, and return value

int calculate(int x, int y) {
    int temp = x * 2 + y * 3;
    return temp;
}

int a = 5;
int b = 10;
int ans = calculate(a, b);
print(ans);
