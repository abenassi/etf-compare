import pandas as pd
import pytest
import yaml

from ahorro import build


def plano(n=200, inicio="2009-01", r=0.003):
    return pd.Series([100 * (1 + r) ** i for i in range(n)], index=pd.period_range(inicio, periods=n, freq="M"))


@pytest.fixture
def config():
    with open("config/instrumentos.yaml") as fh:
        return yaml.safe_load(fh)


def obtener_falso(nombre):
    if "EONIA" in nombre or "EST/" in nombre or "TB3MS" in nombre:
        return pd.Series(2.0, index=pd.period_range("2005-01", periods=260, freq="M"))
    if "EXR" in nombre:
        return pd.Series(1.1, index=pd.period_range("2005-01", periods=260, freq="M"))
    if nombre == "yahoo:IVOA.DE":
        return plano(30, "2023-09")
    return plano()


def instrumentos(vista):
    return [i for g in vista["grupos"] for i in g["instrumentos"]]


def test_build_produce_las_tres_vistas(config):
    out = build.construir(config, obtener_falso)
    assert set(out) == {"es", "ea", "us"}
    g = out["es"]["grupos"]
    assert [x["id"] for x in g] == ["liq", "med", "jub"]
    assert all(sum(bool(i["destacado"]) for i in x["instrumentos"]) == 1 for x in g)
    assert out["es"]["desde"] == "2010-01"
    assert out["us"]["moneda"] == "USD"
    assert len(out["es"]["grafico"]["meses"]) == 121
    assert len(out["es"]["grafico"]["inflacion"]) == 121
    assert [s["grupo"] for s in out["es"]["grafico"]["series"]] == ["liq", "med", "jub"]


def test_build_recorta_al_ultimo_mes_comun(config):
    def corto(n):
        s = obtener_falso(n)
        return s.iloc[:-3] if n.startswith("hicp:") else s

    out = build.construir(config, corto)
    assert out["es"]["datos_al"] == str(plano().index[-4])


def test_build_falla_si_serie_invalida(config):
    def roto(n):
        s = obtener_falso(n)
        if n == "yahoo:VWCE.DE":
            s = s.copy()
            s.iloc[-10] = s.iloc[-11] * 0.04
        return s

    with pytest.raises(ValueError, match="VWCE"):
        build.construir(config, roto)


def test_ivoa_sin_plazos(config):
    ivoa = [i for i in instrumentos(build.construir(config, obtener_falso)["es"]) if i.get("sin_plazos")]
    assert ivoa and ivoa[0]["hoy"]["rinde"] == pytest.approx(0.0369)
    assert ivoa[0]["perdida"] is None and ivoa[0]["escenarios"] is None


def test_cuenta_remunerada_no_pierde_y_tiene_hoy(config):
    cuenta = instrumentos(build.construir(config, obtener_falso)["es"])[0]
    assert cuenta["nombre"] == "Cuenta remunerada"
    assert all(v == 0.0 for v in cuenta["perdida"].values())
    assert cuenta["hoy"]["rinde"] == pytest.approx(0.015)  # 2% - 0,5


def test_hoy_real_y_nota_cuando_pierde_contra_inflacion(config):
    def inflacion_alta(n):
        if n.startswith("hicp:"):
            return plano(r=0.004)  # ~4,9% anual > 3,96% de XZE5
        return obtener_falso(n)

    xze5 = instrumentos(build.construir(config, inflacion_alta)["es"])[2]
    assert xze5["hoy"]["real"] < 0 and xze5["hoy"]["nota"]


def test_build_ipc_con_mes_faltante(config):
    def con_hueco(n):
        s = obtener_falso(n)
        if n == "fred:CPIAUCSL":
            s = s.drop(s.index[-8])  # como octubre de 2025, que BLS no publicó
        return s

    us = build.construir(config, con_hueco)["us"]
    assert us["inflacion_interanual"] == pytest.approx(1.003 ** 12 - 1)
    meses = pd.PeriodIndex(us["grafico"]["meses"], freq="M")
    assert len(meses) == 121 and (meses[1:] - meses[:-1] == meses.freq).all()


def test_build_falla_si_etf_tiene_un_mes_faltante(config):
    def con_hueco(n):
        s = obtener_falso(n)
        return s.drop(s.index[-8]) if n == "yahoo:VT" else s

    with pytest.raises(ValueError, match="VT"):
        build.construir(config, con_hueco)


def test_build_incluye_rendimiento_nominal(config):
    vwce = instrumentos(build.construir(config, obtener_falso)["es"])[5]
    assert vwce["rend_nominal_anual"] == pytest.approx(1.003 ** 12 - 1)
