"""Construcción de la serie de cada instrumento: empalme con proxy, moneda, cuenta modelada y validación."""

import pandas as pd

DESDE = "2010-01"


def empalmar(real: pd.Series, proxy: pd.Series | None, ter_diff: float) -> pd.Series:
    """Antes del primer mes de `real`, encadena hacia atrás los retornos de `proxy` menos `ter_diff` anual."""
    real = real.dropna()
    if proxy is None:
        return real
    inicio = real.index[0]
    previo = proxy.dropna()
    previo = previo[previo.index <= inicio]
    if len(previo) < 2:
        return real
    retornos = previo.pct_change().iloc[1:] - ter_diff / 12
    valores, nivel = [], real.iloc[0]
    for mes, r in reversed(list(retornos.items())):
        nivel = nivel / (1 + r)
        valores.append((mes - 1, nivel))
    antes = pd.Series(dict(reversed(valores)), dtype=float)
    antes.index = pd.PeriodIndex(antes.index, freq="M")
    return pd.concat([antes, real]).sort_index()


def a_moneda(precios: pd.Series, de: str, a: str, eurusd: pd.Series | None) -> pd.Series:
    """`eurusd` = dólares por 1 euro."""
    if de == a:
        return precios
    fx = eurusd.reindex(precios.index)
    if (de, a) == ("USD", "EUR"):
        return (precios / fx).dropna()
    if (de, a) == ("EUR", "USD"):
        return (precios * fx).dropna()
    raise ValueError(f"conversión no soportada: {de} -> {a}")


def cuenta_modelada(tasa_anual_pct: pd.Series, spread: float = 0.5, piso: float = 0.0) -> pd.Series:
    """Índice base 100 de una cuenta remunerada: capitaliza mes a mes max(tasa - spread, piso)."""
    tasa = (tasa_anual_pct.dropna() - spread).clip(lower=piso) / 100 / 12
    crec = 1 + tasa  # la tasa de cada mes es lo que rinde la cuenta durante ese mes
    crec.iloc[0] = 1.0
    return 100 * crec.cumprod()


def validar(nombre: str, s: pd.Series, salto_max: float) -> list[str]:
    errores = []
    if s.empty or s.index[0] > pd.Period(DESDE, freq="M"):
        errores.append(f"{nombre}: no cubre desde {DESDE} (empieza en {s.index[0] if len(s) else '-'})")
    for mes in s.index[s.isna()]:
        errores.append(f"{nombre}: mes vacío en {mes}")
    r = s.dropna().pct_change().iloc[1:]
    for mes, x in r[r.abs() > salto_max].items():
        errores.append(f"{nombre}: salto de {x:+.0%} en {mes} (máximo {salto_max:.0%})")
    return errores


def recortar(series: dict[str, pd.Series], desde: str = DESDE) -> dict[str, pd.Series]:
    inicio = pd.Period(desde, freq="M")
    fin = min(s.dropna().index[-1] for s in series.values())
    return {k: s[(s.index >= inicio) & (s.index <= fin)] for k, s in series.items()}
