import pandas as pd
import pytest

from ahorro import metricas as m


def serie(vals, inicio="2010-01"):
    return pd.Series(list(vals), index=pd.period_range(inicio, periods=len(vals), freq="M"), dtype=float)



def test_pct_perdida_sin_ventanas_es_none():
    assert m.pct_perdida(serie([100, 90, 95, 110, 120]), 1) is None


def test_pct_perdida_cuenta_ventanas():
    p = serie([100] * 6 + [80] * 7 + [130] * 12)  # 25 meses -> 13 ventanas de 12
    esperado = sum(p.iloc[i + 12] < p.iloc[i] for i in range(13)) / 13
    assert esperado > 0
    assert m.pct_perdida(p, 1) == pytest.approx(esperado)


def test_pct_perdida_nunca_es_cero():
    assert m.pct_perdida(serie([100 + i for i in range(40)]), 1) == 0.0



def test_escenarios_peor_tipico_mejor():
    p = serie([100] * 12 + [90, 100, 120])  # 3 ventanas de 12: 90, 100, 120
    assert m.escenarios(p, 1) == pytest.approx({"peor": 9000, "tipico": 10000, "mejor": 12000})


def test_escenarios_sin_ventanas_es_none():
    assert m.escenarios(serie([100] * 5), 1) is None


def test_crecimiento_arranca_en_monto_y_largo():
    c = m.crecimiento(serie([50 + i for i in range(130)]))
    assert len(c) == 121 and c[0] == pytest.approx(10000)
    assert c[-1] == pytest.approx(10000 * 179 / 59)





def test_rendimiento_nominal_anual():
    p = serie([100 * 1.10 ** (i / 12) for i in range(121)])
    assert m.rendimiento_nominal_anual(p) == pytest.approx(0.10, rel=1e-6)


def test_escenarios_son_nominales():
    p = serie([100 * 1.10 ** (i / 12) for i in range(13)])
    assert m.escenarios(p, 1)["peor"] == pytest.approx(11000)
