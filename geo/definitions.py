def soil_phase_diagram() -> None:
    soil_phase_diagram = """
    ┌───────────────────────────────────────────────────────┐
    │                   SOIL PHASE DIAGRAM                  │
    └───────────────────────────────────────────────────────┘

      Weight              Phases                  Volume
    ──────────  ┌────────────────────────┐   ────────────────
      │    │    │                        │     │     │    │
      │   W_a   │          Air           │    V_a    │    │
      │    │    │                        │     │     │    │
      │  ─────  ├────────────────────────┤   ─────  V_v   │
      │    │    │                        │     │     │    │
      W   W_w   │         Water          │    V_w    │    V
      │    │    │                        │     │     │    │
      │  ─────  ├────────────────────────┤   ───────────  │
      │    │    │                        │     │          │
      │   W_s   │         Solids         │    V_s         │
      │    │    │                        │     │          │
    ──────────  └────────────────────────┘   ────────────────

    Notes:
    • W_a = 0  (weight of air neglected)
    • W   = W_s + W_w
    • V_v = V_a + V_w
    • V   = V_s + V_v
    """
    print(soil_phase_diagram)


def unit_weight(weight: float, volume: float) -> float:
    """
    Peso Unitario

        γ = W / V

    Parameters
    ----------
    Weight (W): float
    Volume (V): float

    Returns
    -------
    Unit weight (γ): float
    """
    return weight / volume


def dry_unit_weight(weight_solids: float, total_volume: float) -> float:
    """
    Peso seco unitario

        γ_d = W_s / V

    Parameters
    ----------
    Weight of solids (W_s): float
    Total volume       (V): float

    Returns
    -------
    Dry unit weight (γ_d): float
    """
    return weight_solids / total_volume


def water_unit_weight(water_weight: float = 9.81, water_volume: float = 1) -> float:
    """
    Peso específico del agua

        γ_s = W_w / V_w

    Parameters
    ----------
    Weight: float = 9.81 kN
    Volume: float = 1.00 m³

    Returns
    -------
    Water unit weight (γ_w): float
    """
    return water_weight / water_volume


def buoyant_unit_weight(
    saturated_unit_weight: float, water_unit_weight: float
) -> float:
    """
    Peso específico flotante

        γ_b =  γ_sat / γ_w

    Parameters
    ----------
    Saturated unit weight (γ_sat): float
    Water unit weight       (γ_w): float

    Notes
    -----
    γ_sat is the unit weight, γ, when S = 100%

    Returns
    -------
    Buoyant unit weight (γ_b): float
    """
    return saturated_unit_weight - water_unit_weight


def degree_of_saturation(water_volume: float, void_volume: float) -> float:
    """
    Saturación

        S =  [ V_w / V_v ] * 100%

    Parameters
    ----------
    Volume of water (V_w): float
    Volume of voids (V_v): float

    Returns
    -------
    Degree of saturation (S): float
    """
    return 100 * water_volume / void_volume


def moisture_content(water_weight: float, solids_weight: float) -> float:
    """
    Contenido de humedad

        w =  [ W_w / W_s ] * 100%

    Parameters
    ----------
    Weight of water  (W_w): float
    Weight of solids (W_s): float

    Returns
    -------
    Moisture content (w): float
    """
    return 100 * water_weight / solids_weight


def void_ratio(void_volume: float, solids_volume: float) -> float:
    """
    Relación de vacíos

        e =  V_v / V_s

    Parameters
    ----------
    Volume of voids  (V_v): float
    Volume of solids (V_s): float

    Returns
    -------
    Void ratio (e): float
    """

    return void_volume / solids_volume


def porosity(void_volume: float, total_volume: float) -> float:
    """
    Porosidad

        n =  [ V_v / V ] * 100%

    Parameters
    ----------
    Volume of voids  (V_v): float
    Total volume       (V): float

    Returns
    -------
    Porosity (n): float
    """

    return void_volume / total_volume


def solids_specific_gravity(
    solids_weight: float, solids_volume: float, water_unit_weight: float = 9.81
) -> float:
    """
    Gravedad específica de sólidos

        G_s =  [ W_s / V_s ] / γ_w

    Parameters
    ----------
    Weight of solids  (W_s): float
    Volume of solids  (V_s): float
    Water unit weight (γ_w): float

    Returns
    -------
    Specific gravity of solids (G_s): float
    """
    return (solids_weight / solids_volume) / water_unit_weight


def relative_density(
    void_ratio: float, min_void_ratio: float, max_void_ratio: float
) -> float:
    """
    Densidad relativa (D_r)

        n =    [ e_max / e ]   * 100%
             -----------------
             [ e_max / e_min ]

    Parameters
    ----------
    Void ratio                   (e): float
    Minimum index void ratio (e_min): float
    Maximum index void ratio (e_max): float

    Notes
    -----
    ∙ Only applicable on sands with less than 15% fines
    ∙ e_min is obtained through ASTM D4253
    ∙ e_max is obtained through ASTM D4254

    Returns
    -------
    Relative density (Dr): float
    """
    return 100 * (max_void_ratio - void_ratio) / (max_void_ratio - min_void_ratio)


if __name__ == "__main__":
    soil_phase_diagram()
