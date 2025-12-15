from geo.bearing_capacity import bearing_factors_table


def main():
    df = bearing_factors_table("Terzaghi")
    print(df)


if __name__ == "__main__":
    main()
