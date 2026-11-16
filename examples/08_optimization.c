// Example 8: Code Optimization Demonstration
// Contains constant folding opportunities, algebraic identities,
// copy propagation, and dead code.

int a = 2 + 3 * 4;       // Can be constant folded to 14
int b = a * 1;           // Algebraic identity (b = a)
int c = b + 0;           // Algebraic identity (c = b)
int d = 100 * 0;         // Algebraic identity (d = 0)
int dead = a + 50;       // Dead variable (never used after this)
int ans = c + 5;
