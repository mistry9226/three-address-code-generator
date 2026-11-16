// Example 6: Switch-Case Multiway Branching
// Tests switch value comparison, jump tables/conditional dispatch, and default case

int option = 2;
int action = 0;

switch (option) {
    case 1:
        action = 100;
        break;
    case 2:
        action = 200;
        break;
    case 3:
        action = 300;
        break;
    default:
        action = -1;
        break;
}
