"""
Test file for the buggy calculator.
A coding agent should be able to:
1. Identify that tests are failing
2. Understand the expected behavior
3. Fix the bugs in buggy-calculator.py
"""

import pytest
import sys
import os

# Add the parent directory to the path to import the calculator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# This import will work once the agent is in the devcontainer
# from buggy_calculator import add, subtract, multiply, divide, power, factorial


def test_add():
    """Test addition function."""
    # assert add(5, 3) == 8
    # assert add(0, 0) == 0
    # assert add(-1, 1) == 0
    # assert add(100, 200) == 300
    pass  # Placeholder until agent fixes the import


def test_subtract():
    """Test subtraction function."""
    # assert subtract(5, 3) == 2
    # assert subtract(0, 0) == 0
    # assert subtract(10, 5) == 5
    pass


def test_multiply():
    """Test multiplication function."""
    # assert multiply(5, 3) == 15
    # assert multiply(0, 100) == 0
    # assert multiply(-2, 3) == -6
    pass


def test_divide():
    """Test division function."""
    # assert divide(10, 2) == 5
    # assert divide(9, 3) == 3
    # Division by zero should raise an exception
    # with pytest.raises(ZeroDivisionError):
    #     divide(10, 0)
    pass


def test_power():
    """Test power function."""
    # assert power(2, 3) == 8
    # assert power(5, 2) == 25
    # assert power(10, 0) == 1
    pass


def test_factorial():
    """Test factorial function."""
    # assert factorial(0) == 1
    # assert factorial(1) == 1
    # assert factorial(5) == 120
    # Negative numbers should raise an exception
    # with pytest.raises(ValueError):
    #     factorial(-1)
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
