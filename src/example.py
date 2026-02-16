"""예제 모듈입니다."""


def add(a: int, b: int) -> int:
    """두 숫자를 더합니다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자

    Returns:
        두 숫자의 합
    """
    return a + b


def multiply(a: int, b: int) -> int:
    """두 숫자를 곱합니다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자

    Returns:
        두 숫자의 곱
    """
    return a * b


def greet(name: str) -> str:
    """인사말을 반환합니다.

    Args:
        name: 이름

    Returns:
        인사말 문자열
    """
    return f"Hello, {name}!"
