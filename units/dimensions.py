# units/dimensions.py

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    M: int = 0
    L: int = 0
    T: int = 0

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(self.M + other.M, self.L + other.L, self.T + other.T)

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(self.M - other.M, self.L - other.L, self.T - other.T)

    def is_dimensionless(self) -> bool:
        return self.M == self.L == self.T == 0

    def __repr__(self):
        return f"<Dim M={self.M} L={self.L} T={self.T}>"
