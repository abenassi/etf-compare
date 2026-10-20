"""Cálculos puros sobre series mensuales (índice PeriodIndex mensual, valores de nivel).

Las series llegan ya recortadas al período común; acá no se recorta por fecha.
"""

import pandas as pd

MONTO = 10000


def real(precios: pd.Series, ipc: pd.Series) -> pd.Series:
    """Precio en moneda de hoy: deflactado y con el último mes igual al nominal."""
    return precios / ipc * ipc.iloc[-1]


def rendimiento_real_anual(precios: pd.Series, ipc: pd.Series, meses: int = 120) -> float:
    r = real(precios, ipc).iloc[-meses - 1:]
    return (r.iloc[-1] / r.iloc[0]) ** (12 / (len(r) - 1)) - 1


def rendimiento_nominal_anual(precios: pd.Series, meses: int = 120) -> float:
    p = precios.iloc[-meses - 1:]
    return (p.iloc[-1] / p.iloc[0]) ** (12 / (len(p) - 1)) - 1


def _ratios(s: pd.Series, anios: int) -> pd.Series:
    n = anios * 12
    v = s.to_numpy()
    return pd.Series(v[n:] / v[:-n]) if len(v) > n else pd.Series(dtype=float)


def pct_perdida(precios: pd.Series, anios: int) -> float | None:
    """Fracción de ventanas de `anios` años que terminaron con menos plata nominal de la que se puso."""
    r = _ratios(precios, anios)
    return float((r < 1).mean()) if len(r) else None


def pct_perdida_real(precios: pd.Series, ipc: pd.Series, anios: int) -> float | None:
    """Como pct_perdida, pero contra la inflación: terminaste con menos poder de compra del que pusiste."""
    return pct_perdida(real(precios, ipc), anios)


def escenarios(precios: pd.Series, ipc: pd.Series, anios: int, monto: float = MONTO) -> dict | None:
    """Peor, típico (mediana) y mejor valor final de `monto`, en moneda de hoy."""
    r = _ratios(real(precios, ipc), anios) * monto
    if not len(r):
        return None
    return {"peor": float(r.min()), "tipico": float(r.median()), "mejor": float(r.max())}


def crecimiento(precios: pd.Series, meses: int = 120, monto: float = MONTO) -> list[float]:
    s = precios.iloc[-meses - 1:]
    return [float(x) for x in s / s.iloc[0] * monto]


def inflacion_acumulada(ipc: pd.Series, meses: int = 120, monto: float = MONTO) -> list[float]:
    return crecimiento(ipc, meses, monto)


def inflacion_interanual(ipc: pd.Series) -> float:
    return float(ipc.iloc[-1] / ipc.iloc[-13] - 1)
