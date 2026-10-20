"""Bajada de series (Yahoo, Eurostat, FRED, BCE) con caché CSV versionada en data/raw/."""

import io
import sys
from pathlib import Path
from typing import Callable

import pandas as pd
import requests

DIR_RAW = Path("data/raw")
TIMEOUT = 60


def mensual(s: pd.Series, como: str) -> pd.Series:
    """Pasa una serie con índice de fechas a mensual: 'promedio' (tasas) o 'ultimo' (precios, índices)."""
    s = s.dropna().astype(float)
    g = s.groupby(pd.DatetimeIndex(s.index).to_period("M"))
    out = g.mean() if como == "promedio" else g.last()
    out.index = pd.PeriodIndex(out.index, freq="M")
    return out


def bajar_yahoo(ticker: str) -> pd.Series:
    import yfinance as yf

    df = yf.download(ticker, start="1990-01-01", interval="1mo", auto_adjust=True, progress=False)
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return mensual(close, "ultimo")


def moneda_yahoo(ticker: str) -> str | None:
    """Moneda en la que Yahoo publica los precios del ticker. None si no se pudo consultar (no frena el build)."""
    import yfinance as yf

    try:
        return yf.Ticker(ticker).fast_info["currency"]
    except Exception as e:
        print(f"AVISO: no pude consultar la moneda de {ticker}: {e}", file=sys.stderr)
        return None




def bajar_fred(serie_id: str) -> pd.Series:
    r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie_id}", timeout=TIMEOUT)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    s = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    s.index = pd.to_datetime(df.iloc[:, 0])
    return mensual(s, "promedio")


def bajar_bce(clave: str) -> pd.Series:
    """`clave` = 'FLUJO/RESTO', por ejemplo 'EXR/M.USD.EUR.SP00.E'. Las diarias se promedian por mes."""
    r = requests.get(f"https://data-api.ecb.europa.eu/service/data/{clave}?format=csvdata", timeout=TIMEOUT)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), usecols=["TIME_PERIOD", "OBS_VALUE"])
    s = pd.Series(pd.to_numeric(df["OBS_VALUE"], errors="coerce").to_numpy(),
                  index=pd.to_datetime(df["TIME_PERIOD"]))
    return mensual(s, "promedio")


def parse_bbk(texto: str) -> pd.Series:
    """CSV del Bundesbank: cabecera de metadatos y después filas 'AAAA-MM,valor'. '.' = sin dato."""
    filas = [l.split(",")[:2] for l in texto.splitlines() if len(l) >= 7 and l[:4].isdigit() and l[4] == "-"]
    s = pd.Series({m: pd.to_numeric(v, errors="coerce") for m, v in filas}, dtype=float).dropna()
    s.index = pd.PeriodIndex(s.index, freq="M")
    return s


def bajar_bbk(clave: str) -> pd.Series:
    r = requests.get(f"https://api.statistiken.bundesbank.de/rest/download/{clave}?format=csv&lang=en", timeout=TIMEOUT)
    r.raise_for_status()
    return parse_bbk(r.text)


def _leer(path: Path) -> pd.Series:
    df = pd.read_csv(path, dtype={"mes": str})
    return pd.Series(df["valor"].to_numpy(dtype=float), index=pd.PeriodIndex(df["mes"], freq="M"))


def actualizar(nombre: str, bajar: Callable[[], pd.Series], dir_raw: Path = DIR_RAW) -> pd.Series:
    path = Path(dir_raw) / f"{nombre}.csv"
    cache = _leer(path) if path.exists() else None
    if cache is not None:
        cache = cache[cache.index < pd.Period.now("M")]
    try:
        nueva = bajar().dropna()
        if nueva.empty:
            raise ValueError("la fuente devolvió una serie vacía")
    except Exception as e:  # cualquier falla de red o de formato: seguimos con el caché
        if cache is None:
            raise
        print(f"AVISO: {nombre} sin actualizar: {e}", file=sys.stderr)
        return cache
    s = nueva if cache is None else pd.concat([cache[~cache.index.isin(nueva.index)], nueva]).sort_index()
    s = s[s.index < pd.Period.now("M")]  # el mes en curso todavía no cerró: no se guarda
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"mes": s.index.astype(str), "valor": s.to_numpy()}).to_csv(path, index=False)
    return s
