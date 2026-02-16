"""example 모듈의 테스트입니다."""

import pytest
from src.example import add, multiply, greet


def test_add() -> None:
    """add 함수 테스트"""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_multiply() -> None:
    """multiply 함수 테스트"""
    assert multiply(2, 3) == 6
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0


def test_greet() -> None:
    """greet 함수 테스트"""
    assert greet("World") == "Hello, World!"
    assert greet("AI") == "Hello, AI!"


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 1, 2),
        (10, 20, 30),
        (-5, 5, 0),
    ],
)
def test_add_parametrized(a: int, b: int, expected: int) -> None:
    """파라미터화된 add 함수 테스트"""
    assert add(a, b) == expected
