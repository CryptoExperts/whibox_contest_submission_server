#!/usr/bin/env python3
from dataclasses import dataclass


class NIST_P256:
    p = 115792089210356248762697446949407573530086143415290314195533631308867097853951
    n = 115792089210356248762697446949407573529996955224135760342422259061068512044369

    a = p-3
    b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b

    @dataclass
    class Modular:
        val: int

        def __add__(self, y: "Modular") -> "Modular":
            return NIST_P256.Modular((self.val + y.val) % NIST_P256.p)

        def __sub__(self, y: "Modular") -> "Modular":
            return NIST_P256.Modular((self.val - y.val) % NIST_P256.p)

        def __neg__(self) -> "Modular":
            return NIST_P256.Modular(-self.val)

        def __mul__(self, y: "Modular") -> "Modular":
            return NIST_P256.Modular((self.val * y.val) % NIST_P256.p)

        def __rmul__(self, y: int) -> "Modular":
            return NIST_P256.Modular(y) * self

        def __pow__(self, exp: int) -> "Modular":
            return NIST_P256.Modular(int(pow(self.val, exp, NIST_P256.p)))

        def __truediv__(self, y: "Modular") -> "Modular":
            y_inv = y ** (self.p-2)
            return self * y_inv

        def __eq__(self, y):
            return ((self.val - y.val) % self.p) == 0

        def __repr__(self):
            return f'{self.val:064X}'

    @dataclass
    class Point:
        x: "NIST_P256.Modular"
        y: "NIST_P256.Modular"

        def __add__(self, Q: "Point") -> "Point":
            # either self or Q is the point at infinity
            if self.is_at_infinity:
                return Q
            if Q.is_at_infinity:
                return self

            # self and Q are inverse, including the case where y=0
            if self == -Q:
                return NIST_P256.Point.infinity()

            # normal cases
            if self == Q:  # doubling
                lambda_ = (3 * (self.x ** 2) + self.a) / (2*self.y)
            else:          # add
                lambda_ = (Q.y - self.y) / (Q.x - self.x)

            R_x = (lambda_ ** 2) - self.x - Q.x
            R_y = lambda_ * (self.x - R_x) - self.y
            return NIST_P256.Point(R_x, R_y)

        def __eq__(self, Q):
            return self.x == Q.x and self.y == Q.y

        def __neg__(self) -> "Point":
            return NIST_P256.Point(self.x, -self.y)

        def __sub__(self, Q: "Point") -> "Point":
            return self + (-Q)

        def __rmul__(self, scalar: int) -> "Point":
            R = NIST_P256.Point(0, 0)

            for i, b in enumerate(bin(scalar)[2:]):
                R = R + R
                if int(b):      # adding
                    R = self + R

            return R

        def __repr__(self):
            return f"x = {self.x}, y = {self.y}"

        def __str__(self):
            return f"{self.x}{self.y}"

        @property
        def is_at_infinity(self):
            return self.x == self.y == 0

        @property
        def is_on_curve(self):
            return self.y ** 2 == self.x**3 + self.a*self.x + self.b

        @classmethod
        def infinity(cls):
            return NIST_P256.Point(0, 0)

    G = Point(
        Modular(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296),
        Modular(0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
    )
    Point.a = Modular(a)
    Point.b = Modular(b)
    Modular.p = p

    @classmethod
    def scalar_multiplication(cls, scalar: int, P: Point = None) -> Point:
        if not P:
            P = cls.G
        return scalar * P


if __name__ == "__main__":
    P = NIST_P256.scalar_multiplication(
        12078056106883488161242983286051341125085761470677906721917479268909056)
    print(P)
