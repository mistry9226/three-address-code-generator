// Example 5: 1D and 2D Array Operations
// Demonstrates row-major address calculation:
// 1D: base + (i * width)
// 2D: base + ((i * N + j) * width)

int A[10];
int matrix[4][5];
int i = 2;
int j = 3;
int val = 42;

// 1D Array Access
A[i] = val;
val = A[i] + 10;

// 2D Array Access (Row-Major: (i * 5 + j) * 4)
matrix[i][j] = val * 2;
int result = matrix[i][j] + A[i];
