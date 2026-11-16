// Example 4: For Loop with Break and Continue
// Tests loop initialization, step, continue target, and break exit

int total = 0;

for (int k = 0; k < 15; k++) {
    if (k == 5) {
        continue;
    }
    if (k > 10) {
        break;
    }
    total += k;
}
