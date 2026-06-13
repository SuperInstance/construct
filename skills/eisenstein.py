#!/usr/bin/env python3
"""
eisenstein.py — Eisenstein Integer Computation Skill
====================================================

Tank upload: "I know Eisenstein integers."

Provides Eisenstein integer arithmetic: norm, multiplication, division,
GCD, and factorization over the Eisenstein integers Z[ω] where ω = e^(2πi/3).

The norm form N(a + bω) = a² − ab + b² is central to constraint theory.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ω = e^(2πi/3) = (-1 + i√3) / 2
# An Eisenstein integer is a + bω where a, b ∈ Z

@dataclass
class EisensteinInt:
    """An Eisenstein integer a + bω."""
    a: int
    b: int

    def __repr__(self) -> str:
        if self.b == 0:
            return str(self.a)
        if self.a == 0:
            if self.b == 1:
                return "ω"
            return f"{self.b}ω"
        sign = "+" if self.b > 0 else "-"
        return f"{self.a} {sign} {abs(self.b)}ω"

    def __eq__(self, other) -> bool:
        if isinstance(other, EisensteinInt):
            return self.a == other.a and self.b == other.b
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.a, self.b))

    @property
    def norm(self) -> int:
        """Compute N(a + bω) = a² − ab + b²."""
        return self.a * self.a - self.a * self.b + self.b * self.b

    def conjugate(self) -> "EisensteinInt":
        """Conjugate: (a + bω)̄ = (a − b) − bω."""
        return EisensteinInt(self.a - self.b, -self.b)

    def __add__(self, other: "EisensteinInt") -> "EisensteinInt":
        return EisensteinInt(self.a + other.a, self.b + other.b)

    def __sub__(self, other: "EisensteinInt") -> "EisensteinInt":
        return EisensteinInt(self.a - other.a, self.b - other.b)

    def __mul__(self, other: "EisensteinInt") -> "EisensteinInt":
        """Multiply: (a + bω)(c + dω) = (ac − bd) + (ad + bc − bd)ω."""
        a, b = self.a, self.b
        c, d = other.a, other.b
        return EisensteinInt(a * c - b * d, a * d + b * c - b * d)

    def is_unit(self) -> bool:
        """Check if this is a unit (norm = 1)."""
        return self.norm == 1

    def divides(self, other: "EisensteinInt") -> bool:
        """Check if self divides other."""
        if self.norm == 0:
            return other.norm == 0
        try:
            q = other / self
            return q is not None
        except (ZeroDivisionError, ValueError):
            return False

    def __truediv__(self, other: "EisensteinInt") -> "EisensteinInt":
        """Divide with exact quotient check."""
        if other.norm == 0:
            raise ZeroDivisionError("Division by zero Eisenstein integer")

        # (a + bω) / (c + dω) = (a + bω)(c + dω)̄ / N(c + dω)
        conj = other.conjugate()
        numerator = self * conj
        norm = other.norm

        # Check exact division
        if numerator.a % norm != 0 or numerator.b % norm != 0:
            raise ValueError(f"Not exactly divisible: {self} / {other}")

        return EisensteinInt(numerator.a // norm, numerator.b // norm)


def eisenstein_norm(a: int, b: int) -> int:
    """Compute Eisenstein norm N(a + bω) = a² − ab + b²."""
    return a * a - a * b + b * b


def eisenstein_multiply(a1: int, b1: int, a2: int, b2: int) -> Tuple[int, int]:
    """Multiply two Eisenstein integers. Returns (a, b) of result."""
    z1 = EisensteinInt(a1, b1)
    z2 = EisensteinInt(a2, b2)
    result = z1 * z2
    return result.a, result.b


def eisenstein_divide(a1: int, b1: int, a2: int, b2: int) -> Tuple[int, int]:
    """Divide two Eisenstein integers. Returns (a, b) of quotient or raises ValueError."""
    z1 = EisensteinInt(a1, b1)
    z2 = EisensteinInt(a2, b2)
    result = z1 / z2
    return result.a, result.b


def eisenstein_gcd(a1: int, b1: int, a2: int, b2: int) -> Tuple[int, int]:
    """GCD of two Eisenstein integers using Euclidean algorithm."""
    z1 = EisensteinInt(a1, b1)
    z2 = EisensteinInt(a2, b2)

    while z2.norm > 0:
        # Division in Z[ω] always has a quotient within distance 1
        # (a + bω) = q(c + dω) + r where N(r) < N(c + dω)
        conj = z2.conjugate()
        num = z1 * conj
        norm = z2.norm

        # Round to nearest integer for quotient
        qa = round(num.a / norm) if norm != 0 else 0
        qb = round(num.b / norm) if norm != 0 else 0
        q = EisensteinInt(qa, qb)
        r = z1 - q * z2

        z1 = z2
        z2 = r

    return z1.a, z1.b


def is_eisenstein_prime(a: int, b: int) -> bool:
    """Check if an Eisenstein integer is prime."""
    n = eisenstein_norm(a, b)
    if n <= 1:
        return False
    # A rational prime p ≡ 2 (mod 3) remains prime in Z[ω]
    # Check if norm is a rational prime
    return _is_rational_prime(n)


def _is_rational_prime(n: int) -> bool:
    """Simple primality test."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


# Unit group: {1, -1, ω, -ω, ω², -ω²}
UNITS = [
    EisensteinInt(1, 0),    # 1
    EisensteinInt(-1, 0),   # -1
    EisensteinInt(0, 1),    # ω
    EisensteinInt(0, -1),   # -ω
    EisensteinInt(-1, 1),   # ω² = -1 + ω
    EisensteinInt(1, -1),   # -ω² = 1 - ω
]
