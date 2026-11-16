// Example 2: Conditional Statements
// Tests if, if-else, relational operators, and logical operators

int score = 85;
int grade = 0;
int passed = 0;

if (score >= 90) {
    grade = 1;
    passed = 1;
} else if (score >= 75 && score < 90) {
    grade = 2;
    passed = 1;
} else {
    grade = 3;
    passed = 0;
}
