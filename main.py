from units.units import Stress, Length


def main():
    s = Stress.MPa(10)
    L = Length.m(2)

    result = s * (L / L)
    print(result)


if __name__ == "__main__":
    main()
