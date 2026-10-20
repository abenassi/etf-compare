import json

import pandas as pd
import pytest
import yaml

from ahorro import build


def plano(n=330, inicio="1998-01", r=0.003):
    return pd.Series([100 * (1 + r) ** i for i in range(n)], index=pd.period_range(inicio, periods=n, freq="M"))


@pytest.fixture
def config():
    with open("config/instrumentos.yaml") as fh:
        return yaml.safe_load(fh)


def obtener_falso(nombre):
    if "EONIA" in nombre or "EST/" in nombre or "TB3MS" in nombre:
        return pd.Series(2.0, index=pd.period_range("1995-01", periods=380, freq="M"))
    if "EXR" in nombre:
        return pd.Series(1.1, index=pd.period_range("1995-01", periods=380, freq="M"))
    if nombre.startswith("bbk:"):
        return pd.Series(3.0, index=pd.period_range("1995-01", periods=380, freq="M"))
    if nombre == "yahoo:IVOA.DE":
        return plano(30, "2023-09")
    return plano()


def instrumentos(vista):
    return [i for g in vista["grupos"] for i in g["instrumentos"]]


def test_build_produce_vistas_euro_y_dolar(config):
    out = build.construir(config, obtener_falso)
    assert set(out) == {"eur", "usd"}
    assert out["eur"]["moneda"] == "EUR" and out["usd"]["moneda"] == "USD"
    g = out["eur"]["grupos"]
    assert [x["id"] for x in g] == ["liq", "med", "jub"]
    assert all(sum(bool(i["destacado"]) for i in x["instrumentos"]) == 1 for x in g)
    assert out["eur"]["desde"] == "2000-01"


def test_json_no_menciona_inflacion(config):
    out = build.construir(config, obtener_falso)
    texto = json.dumps(out, ensure_ascii=False).lower()
    assert "infl" not in texto and "real_anual" not in texto


def test_build_recorta_al_ultimo_mes_comun(config):
    def corto(n):
        s = obtener_falso(n)
        return s.iloc[:-3] if n == "yahoo:VT" else s

    out = build.construir(config, corto)
    assert out["usd"]["datos_al"] == str(plano().index[-4])


def test_build_falla_si_serie_invalida(config):
    def roto(n):
        s = obtener_falso(n)
        if n == "yahoo:VWCE.DE":
            s = s.copy()
            s.iloc[-10] = s.iloc[-11] * 0.04
        return s

    with pytest.raises(ValueError, match="VWCE"):
        build.construir(config, roto)


def test_build_falla_si_etf_tiene_un_mes_faltante(config):
    def con_hueco(n):
        s = obtener_falso(n)
        return s.drop(s.index[-8]) if n == "yahoo:VT" else s

    with pytest.raises(ValueError, match="VT"):
        build.construir(config, con_hueco)


def test_ivoa_sin_plazos(config):
    ivoa = [i for i in instrumentos(build.construir(config, obtener_falso)["eur"]) if i.get("sin_plazos")]
    assert ivoa and ivoa[0]["hoy"]["rinde"] == pytest.approx(0.0369)
    assert ivoa[0]["perdida"] is None and ivoa[0]["escenarios"] is None


def test_cuenta_remunerada_no_pierde_y_tiene_hoy(config):
    cuenta = instrumentos(build.construir(config, obtener_falso)["eur"])[0]
    assert cuenta["nombre"] == "Cuenta remunerada"
    assert all(v == 0.0 for v in cuenta["perdida"].values())
    assert cuenta["hoy"]["rinde"] == pytest.approx(0.015)  # 2% - 0,5
    assert set(cuenta["hoy"]) == {"rinde", "fecha", "fuente"}


def test_build_incluye_rendimiento_nominal(config):
    vwce = instrumentos(build.construir(config, obtener_falso)["eur"])[5]
    assert vwce["rend_anual"] == pytest.approx(1.003 ** 12 - 1)


def test_instrumento_con_proxy_dice_que_hay_antes(config):
    xze5 = instrumentos(build.construir(config, obtener_falso)["eur"])[2]
    assert "alemán" in xze5["antes"]


def test_activo_en_dolares_se_convierte_a_euros(config):
    """Con el euro duplicándose contra el dólar, un activo en USD plano tiene que caer a la mitad medido en euros."""
    def euro_fuerte(n):
        if "EXR" in n:
            idx = pd.period_range("1995-01", periods=380, freq="M")
            return pd.Series([1.0 + i / 379 for i in range(380)], index=idx)  # de 1,0 a 2,0 USD por EUR
        if n in ("yahoo:VTSMX", "yahoo:VGTSX", "yahoo:ACWI"):
            return plano(r=0.0)
        if n == "yahoo:VWCE.DE":
            return plano(r=0.0).loc["2019-07":]
        return obtener_falso(n)

    vwce = instrumentos(build.construir(config, euro_fuerte)["eur"])[5]
    assert vwce["nombre"] == "Acciones de todo el mundo"
    assert vwce["perdida"]["10"] == 1.0  # antes de 2019 viene de proxies en USD: en euros siempre perdió


def test_build_falla_si_la_moneda_declarada_no_coincide(config):
    with pytest.raises(ValueError, match="CSPX.AS"):
        build.construir(config, obtener_falso, moneda_de=lambda t: "USD")


def test_build_acepta_monedas_correctas(config):
    reales = {"CSPX.AS": "EUR", "CNDX.AS": "EUR"}

    def moneda_de(t):
        return reales.get(t, "EUR" if t.endswith(".DE") else "USD")

    assert build.construir(config, obtener_falso, moneda_de=moneda_de)


def test_build_embudo_por_plazo(config):
    emb = build.construir(config, obtener_falso)["eur"]["embudo"]
    assert emb["plazos"] == list(range(1, 16))
    assert [s["grupo"] for s in emb["series"]] == ["med", "jub"]
    jub = emb["series"][1]
    assert len(jub["peor"]) == len(jub["tipico"]) == len(jub["mejor"]) == 15
    assert all(p <= t <= m for p, t, m in zip(jub["peor"], jub["tipico"], jub["mejor"]))
    assert len(jub["pierde"]) == 15 and all(0 <= x <= 1 for x in jub["pierde"])


def test_build_historia_desde_el_inicio(config):
    out = build.construir(config, obtener_falso)["eur"]
    h = out["historia"]
    assert h["meses"][0] == "2000-01" and h["meses"][-1] == out["datos_al"]
    assert [s["grupo"] for s in h["series"]] == ["liq", "med", "jub"]
    assert all(len(s["valores"]) == len(h["meses"]) and s["valores"][0] == pytest.approx(10000) for s in h["series"])


def test_historia_liquidez_usa_el_fondo_monetario(config):
    h = build.construir(config, obtener_falso)["eur"]["historia"]
    liq = next(x for x in h["series"] if x["grupo"] == "liq")
    meses = len(h["meses"]) - 1
    assert liq["valores"][-1] == pytest.approx(10000 * 1.003 ** meses)  # XEON (plano), no la cuenta al 1,5%
