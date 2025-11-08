"""
Buggy Calculator - Test file for coding agents to fix

This calculator has several intentional bugs that a coding agent should be able to identify and fix.
"""

def add(a, b):
    """Add two numbers."""
    return a - b  # BUG: Should be addition, not subtraction

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a + b  # BUG: Should be multiplication, not addition

def divide(a, b):
    """Divide a by b."""
    return a / b  # BUG: No zero division check

def power(a, b):
    """Raise a to the power of b."""
    result = 1
    for i in range(b):
        result = result * a
    return result

def factorial(n):
    """Calculate factorial of n."""
    if n == 0:
        return 1
    return n * factorial(n - 1)  # BUG: Missing check for negative numbers

def main():
    """Test the calculator functions."""
    print("Testing Calculator Functions:")
    print(f"5 + 3 = {add(5, 3)}")  # Should be 8, but will be 2
    print(f"5 - 3 = {subtract(5, 3)}")  # Correct: 2
    print(f"5 * 3 = {multiply(5, 3)}")  # Should be 15, but will be 8
    print(f"10 / 2 = {divide(10, 2)}")  # Correct: 5.0
    print(f"2 ^ 3 = {power(2, 3)}")  # Correct: 8
    print(f"5! = {factorial(5)}")  # Correct: 120

if __name__ == "__main__":
    main()
