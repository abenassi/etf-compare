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


def mezcla(componentes: list[pd.Series], pesos: list[float]) -> pd.Series:
    """Cartera con rebalanceo mensual: índice base 100 con el promedio ponderado de los retornos."""
    df = pd.concat(componentes, axis=1).dropna()
    r = (df.pct_change().iloc[1:] * pesos).sum(axis=1)
    return 100 * pd.concat([pd.Series([1.0], index=df.index[:1]), 1 + r]).cumprod()


def bono_sintetico(rendimiento_pct: pd.Series, duracion: float) -> pd.Series:
    """Índice base 100 de un bono a plazo constante: devenga la tasa y pierde duración × suba de tasa."""
    y = rendimiento_pct.dropna() / 100
    r = y.shift(1) / 12 - duracion * y.diff()
    r.iloc[0] = 0.0
    return 100 * (1 + r).cumprod()


def fondo_de_tasa(tasa_anual_pct: pd.Series, ter: float = 0.0) -> pd.Series:
    """Fondo monetario que replica la tasa overnight menos su comisión, incluso con tasas negativas."""
    return cuenta_modelada(tasa_anual_pct, spread=ter * 100, piso=-100.0)


def validar(nombre: str, s: pd.Series, salto_max: float, desde: str = DESDE) -> list[str]:
    errores = []
    if s.empty or s.index[0] > pd.Period(desde, freq="M"):
        errores.append(f"{nombre}: no cubre desde {desde} (empieza en {s.index[0] if len(s) else '-'})")
    for mes in s.index[s.isna()]:
        errores.append(f"{nombre}: mes vacío en {mes}")
    r = s.dropna().pct_change().iloc[1:]
    for mes, x in r[r.abs() > salto_max].items():
        errores.append(f"{nombre}: salto de {x:+.0%} en {mes} (máximo {salto_max:.0%})")
    return errores


def recortar(series: dict[str, pd.Series], desde: str = DESDE) -> dict[str, pd.Series]:
    inicio = pd.Period(desde, freq="M")
    fin = min(s.dropna().index[-1] for s in series.values())
    meses = pd.period_range(inicio, fin, freq="M")
    # reindexar: un mes que falta en la fuente queda como NaN visible, no como un salto silencioso de índice
    return {k: s.reindex(meses) for k, s in series.items()}


def completar_ipc(ipc: pd.Series) -> tuple[pd.Series, list[str]]:
    """Interpola en escala logarítmica los meses faltantes del IPC (p. ej. un mes que el organismo no publicó)."""
    faltan = [str(m) for m in ipc.index[ipc.isna()]]
    if not faltan:
        return ipc, []
    import numpy as np
    out = pd.Series(np.exp(np.log(ipc).interpolate(limit_area="inside")), index=ipc.index)
    return out, [f"IPC sin dato en {', '.join(faltan)}: interpolado"]
