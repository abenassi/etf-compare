import pandas as pd
import pytest

from ahorro import series as s


def serie(vals, inicio="2010-01"):
    return pd.Series(list(vals), index=pd.period_range(inicio, periods=len(vals), freq="M"), dtype=float)


def test_empalmar_encadena_proxy_hacia_atras():
    proxy = serie([10, 11, 12.1, 13.31])
    real = serie([200, 220], inicio="2010-03")
    out = s.empalmar(real, proxy, ter_diff=0.0)
    assert list(out) == pytest.approx([200 / 1.21, 200 / 1.1, 200, 220])
    assert str(out.index[0]) == "2010-01"


def test_empalmar_descuenta_ter():
    out = s.empalmar(serie([100], inicio="2010-02"), serie([10, 10]), ter_diff=0.12)
    # un mes de proxy plano menos 1% mensual: el mes anterior vale más
    assert out.iloc[0] == pytest.approx(100 / (1 - 0.01))


def test_empalmar_sin_proxy_devuelve_real():
    r = serie([1, 2])
    assert s.empalmar(r, None, 0.0).equals(r)


def test_a_moneda_convierte_usd_a_eur():
    p = serie([110, 120]); fx = serie([1.10, 1.20])
    assert list(s.a_moneda(p, "USD", "EUR", fx)) == pytest.approx([100, 100])


def test_a_moneda_convierte_eur_a_usd():
    assert list(s.a_moneda(serie([100]), "EUR", "USD", serie([1.10]))) == pytest.approx([110])


def test_a_moneda_misma_moneda_no_cambia():
    p = serie([1, 2])
    assert s.a_moneda(p, "EUR", "EUR", None).equals(p)


def test_cuenta_modelada_respeta_piso():
    idx = s.cuenta_modelada(serie([-0.5, -0.5, 3.0]))
    assert idx.iloc[0] == 100
    assert idx.iloc[1] == idx.iloc[0]
    assert idx.iloc[2] == pytest.approx(idx.iloc[1] * (1 + 0.025 / 12))


def test_validar_detecta_salto():
    errores = s.validar("SPYI", serie([100, 101, 4, 4.1]), salto_max=0.35)
    assert len(errores) == 1 and "SPYI" in errores[0]


def test_validar_serie_sana_sin_errores():
    assert s.validar("X", serie([100, 101, 102]), salto_max=0.15) == []


def test_validar_detecta_falta_de_cobertura():
    assert s.validar("X", serie([1, 2], inicio="2015-01"), 0.35)


def test_validar_detecta_hueco():
    assert any("vacío" in e for e in s.validar("X", serie([1, float("nan"), 1]), 0.35))


def test_recortar_al_ultimo_mes_comun():
    out = s.recortar({"a": serie(range(1, 30), "2009-06"), "b": serie(range(1, 20))})
    assert all(str(x.index[0]) == "2010-01" and str(x.index[-1]) == "2011-07" for x in out.values())
