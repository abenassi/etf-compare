import pandas as pd
import pytest

from ahorro import metricas as m


def serie(vals, inicio="2010-01"):
    return pd.Series(list(vals), index=pd.period_range(inicio, periods=len(vals), freq="M"), dtype=float)


def test_rendimiento_real_anual_crecimiento_constante():
    p = serie([100 * 1.10 ** (i / 12) for i in range(121)])
    ipc = serie([100 * 1.02 ** (i / 12) for i in range(121)])
    assert m.rendimiento_real_anual(p, ipc) == pytest.approx(1.10 / 1.02 - 1, rel=1e-6)


def test_pct_perdida_sin_ventanas_es_none():
    assert m.pct_perdida(serie([100, 90, 95, 110, 120]), 1) is None


def test_pct_perdida_cuenta_ventanas():
    p = serie([100] * 6 + [80] * 7 + [130] * 12)  # 25 meses -> 13 ventanas de 12
    esperado = sum(p.iloc[i + 12] < p.iloc[i] for i in range(13)) / 13
    assert esperado > 0
    assert m.pct_perdida(p, 1) == pytest.approx(esperado)


def test_pct_perdida_nunca_es_cero():
    assert m.pct_perdida(serie([100 + i for i in range(40)]), 1) == 0.0


def test_escenarios_en_moneda_de_hoy():
    p = serie([100] * 25)
    ipc = serie([100 * 1.10 ** (i / 12) for i in range(25)])
    e = m.escenarios(p, ipc, 1)
    assert e["peor"] == pytest.approx(10000 / 1.10, rel=1e-6)
    assert e["peor"] == pytest.approx(e["tipico"]) == pytest.approx(e["mejor"])


def test_escenarios_peor_tipico_mejor():
    p = serie([100] * 12 + [90, 100, 120])  # 3 ventanas de 12: 90, 100, 120
    ipc = serie([100] * 15)
    assert m.escenarios(p, ipc, 1) == pytest.approx({"peor": 9000, "tipico": 10000, "mejor": 12000})


def test_escenarios_sin_ventanas_es_none():
    assert m.escenarios(serie([100] * 5), serie([100] * 5), 1) is None


def test_crecimiento_arranca_en_monto_y_largo():
    c = m.crecimiento(serie([50 + i for i in range(130)]))
    assert len(c) == 121 and c[0] == pytest.approx(10000)
    assert c[-1] == pytest.approx(10000 * 179 / 59)


def test_inflacion_acumulada():
    ipc = serie([100] * 120 + [110])
    c = m.inflacion_acumulada(ipc)
    assert len(c) == 121 and c[0] == pytest.approx(10000) and c[-1] == pytest.approx(11000)


def test_inflacion_interanual():
    assert m.inflacion_interanual(serie([100] * 12 + [105])) == pytest.approx(0.05)


def test_real_deflacta_y_conserva_ultimo_valor():
    r = m.real(serie([100, 110]), serie([100, 110]))
    assert list(r) == pytest.approx([110, 110])
