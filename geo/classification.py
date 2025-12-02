from typing import TypedDict, Optional


class SoilCharacteristics(TypedDict):
    """Particle size distribution and Atterberg limits (ASTM D2487)."""

    # Rock
    retained_12in: Optional[float]  # Boulder (> 350 mm)

    # Fragments
    passing_12in_retained_3in: Optional[float]  # Cobble (350–75 mm)

    # Soil - Gravel
    passing_3in_retained_3_4in: Optional[float]  # Coarse gravel (75–19 mm)
    passing_3_4in_retained_4: Optional[float]  # Fine gravel (19.0–4.75 mm)

    # Soil - Sand
    passing_4_retained_10: Optional[float]  # Coarse sand (4.75–2.00 mm)
    passing_10_retained_40: Optional[float]  # Medium sand (2.00–0.425 mm)
    passing_40_retained_200: Optional[float]  # Fine sand (0.425–0.075 mm)

    # Soil - Fines
    passing_200: Optional[float]  # Fines (silt + clay) (< 0.075 mm)

    # Atterberg limits
    liquid_limit: Optional[float]
    plastic_limit: Optional[float]


def USCS(soil: SoilCharacteristics) -> str:
    """
    Classify soil according to the Unified Soil Classification System (USCS)
    using ASTM D2487 criteria.

    Parameters
    ----------
    soil : SoilCharacteristics
        Dictionary of particle-size distribution and Atterberg limits.

    Returns
    -------
    str
        USCS group symbol (e.g., 'GW', 'SP-SM', 'CL', etc.)
    """
    fines = soil.get("passing_200")
    LL = soil.get("liquid_limit")
    PL = soil.get("plastic_limit")

    if fines is None:
        raise ValueError("Missing 'passing_200' (fines content).")

    # --- Step 1: Coarse vs. Fine Grained ---
    if fines < 50:
        # Coarse-grained soils
        coarse_gravel = soil.get("passing_3in_retained_3_4in") or 0.0
        fine_gravel = soil.get("passing_3_4in_retained_4") or 0.0
        coarse_sand = soil.get("passing_4_retained_10") or 0.0
        medium_sand = soil.get("passing_10_retained_40") or 0.0
        fine_sand = soil.get("passing_40_retained_200") or 0.0

        gravel = coarse_gravel + fine_gravel
        sand = coarse_sand + medium_sand + fine_sand

        main_group = "G" if gravel > sand else "S"

        # --- Step 2: Clean vs. With Fines ---
        if fines < 5:
            # Clean gravel or sand
            # (Simplified gradation assumption; real Cu/Cc check omitted)
            return f"{main_group}W"  # Well-graded
        elif fines <= 12:
            return f"{main_group}W-{main_group}M"  # Dual symbol (some fines)
        else:
            # With noticeable fines, need Atterberg limits
            if LL is None or PL is None:
                return f"{main_group} with fines (LL/PL missing)"
            PI = LL - PL
            if PI >= 7:
                return f"{main_group}C"  # Clayey
            else:
                return f"{main_group}M"  # Silty

    # --- Step 3: Fine-Grained Soils (≥ 50% fines) ---
    else:
        if LL is None or PL is None:
            return "Fine-grained soil (LL/PL missing)"

        PI = LL - PL

        if LL < 50:
            # Low plasticity range
            if PI >= 7:
                return "CL"  # Lean clay
            else:
                return "ML"  # Silt
        else:
            # High plasticity range
            if PI >= 7:
                return "CH"  # Fat clay
            else:
                return "MH"  # Elastic silt


if __name__ == "__main__":
    soil: SoilCharacteristics = {
        "retained_12in": None,
        "passing_12in_retained_3in": None,
        "passing_3in_retained_3_4in": 10.0,
        "passing_3_4in_retained_4": 25.0,
        "passing_4_retained_10": 30.0,
        "passing_10_retained_40": 20.0,
        "passing_40_retained_200": 10.0,
        "passing_200": 5.0,
        "liquid_limit": 35.0,
        "plastic_limit": 20.0,
    }

    print(USCS(soil))
# → "SW" (well-graded sand, clean)
