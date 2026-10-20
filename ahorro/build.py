"""Orquesta el pipeline: configuración -> series -> métricas -> site/data/{vista}.json."""

import json
import sys
from pathlib import Path
from typing import Callable

import pandas as pd
import yaml

from ahorro import fuentes, metricas, series

PLAZOS = (1, 3, 5, 10)
NOTA_HOY = "Hoy la inflación está alta: esto protege la mayor parte de tu plata, no toda."


def _tasa(config: dict, set_: str, obtener: Callable[[str], pd.Series]) -> pd.Series:
    """Tasa de referencia empalmada: cada fuente pisa a la anterior desde su primer mes."""
    out = None
    for nombre in config["tasas"][set_]:
        s = obtener(nombre).dropna()
        out = s if out is None else pd.concat([out[out.index < s.index[0]], s])
    return out


def _proxy(p: dict, config: dict, obtener) -> pd.Series:
    """Serie del proxy en su moneda de cotización, según su tipo (ver cabecera de instrumentos.yaml)."""
    if "yahoo" in p:
        return obtener(f"yahoo:{p['yahoo']}")
    if "mezcla" in p:
        return series.mezcla([obtener(f"yahoo:{c['yahoo']}") for c in p["mezcla"]], [c["peso"] for c in p["mezcla"]])
    if "bono" in p:
        return series.bono_sintetico(obtener(p["bono"]), p["duracion"])
    if "tasa" in p:
        return series.fondo_de_tasa(_tasa(config, p["tasa"], obtener), p.get("ter", 0.0))
    raise ValueError(f"proxy desconocido: {p}")


def _serie_etf(inst: dict, moneda: str, fx: pd.Series, config: dict, obtener) -> pd.Series:
    real = series.a_moneda(obtener(f"yahoo:{inst['yahoo']}"), inst["moneda_cotiza"], moneda, fx)
    for p in inst.get("proxy") or []:
        proxy = series.a_moneda(_proxy(p, config, obtener), p["moneda_cotiza"], moneda, fx)
        # un proxy "tasa" ya descuenta su comisión; los demás llevan ter_diff
        real = series.empalmar(real, proxy, p.get("ter_diff", 0.0))
    return real


def _hoy(inst: dict, tasa: pd.Series, cuenta_cfg: dict, infl: float) -> dict | None:
    h = inst.get("hoy")
    if inst.get("tipo") == "cuenta":
        rinde, fecha = max(tasa.iloc[-1] - cuenta_cfg["spread"], cuenta_cfg["piso"]) / 100, str(tasa.index[-1])
    elif h and h.get("tasa"):
        rinde, fecha = tasa.iloc[-1] / 100 - h.get("ter", 0.0), str(tasa.index[-1])
    elif h and "ytm" in h:
        rinde, fecha = h["ytm"], h["fecha"]
    else:
        return None
    real = (1 + rinde) / (1 + infl) - 1
    return {"rinde": rinde, "fecha": fecha, "real": real, "nota": NOTA_HOY if real < 0 else None,
            "fuente": (h or {}).get("fuente")}


def _publico(inst: dict) -> dict:
    return {"nombre": inst["nombre"], "detalle": inst["detalle"], "destacado": bool(inst.get("destacado")),
            "ticker": inst.get("yahoo"), "sin_plazos": bool(inst.get("sin_plazos")), "vence": inst.get("vence"),
            "antes": inst.get("antes", "el índice que replica")}


def _vista(clave: str, config: dict, obtener) -> tuple[dict, list[str]]:
    v = config["vistas"][clave]
    moneda, set_ = v["moneda"], config["sets"][v["set"]]
    fx = obtener(config["fx"])
    tasa = _tasa(config, v["set"], obtener)
    cuenta = config["cuenta"]
    ipc = obtener(v["ipc"]).dropna()

    errores, crudas, aparte = [], {"__ipc__": ipc}, {}
    for gid, insts in set_.items():
        for j, inst in enumerate(insts):
            k = f"{gid}:{j}"
            if inst.get("tipo") == "cuenta":
                crudas[k] = series.cuenta_modelada(tasa, cuenta["spread"], cuenta["piso"])
                continue
            s = _serie_etf(inst, moneda, fx, config, obtener)
            if inst.get("sin_plazos"):
                aparte[k] = s
                continue
            errores += series.validar(f"{inst['detalle'].split(' · ')[0]} ({inst['yahoo']})", s, inst["salto_max"],
                                      config["desde"])
            crudas[k] = s
    if errores:
        return {}, [f"[{clave}] {e}" for e in errores]

    rec = series.recortar(crudas, config["desde"])
    ipc_r, avisos = series.completar_ipc(rec.pop("__ipc__"))
    for a in avisos:
        print(f"AVISO: [{clave}] {a}", file=sys.stderr)
    nombres = {f"{g}:{j}": i.get("yahoo") or i["nombre"] for g, insts in set_.items() for j, i in enumerate(insts)}
    huecos = [f"[{clave}] {nombres[k]}: mes vacío en {m}" for k, s in rec.items() for m in s.index[s.isna()]]
    if huecos or ipc_r.isna().any():
        return {}, huecos or [f"[{clave}] IPC con huecos en los extremos"]
    infl = metricas.inflacion_interanual(ipc_r)

    grupos, grafico = [], {"meses": [str(m) for m in ipc_r.index[-121:]],
                           "inflacion": metricas.inflacion_acumulada(ipc_r), "series": []}
    for g in config["grupos"]:
        out = []
        for j, inst in enumerate(set_[g["id"]]):
            k = f"{g['id']}:{j}"
            d = _publico(inst)
            d["hoy"] = _hoy(inst, tasa, cuenta, infl)
            if k in aparte:
                d |= {"real_desde": str(aparte[k].index[0]), "rend_real_anual": None, "rend_nominal_anual": None,
                      "perdida": None, "escenarios": None}
            else:
                p = rec[k]
                d |= {"real_desde": None if inst.get("tipo") == "cuenta" else
                      str(obtener(f"yahoo:{inst['yahoo']}").dropna().index[0]),
                      "rend_real_anual": metricas.rendimiento_real_anual(p, ipc_r),
                      "rend_nominal_anual": metricas.rendimiento_nominal_anual(p),
                      "perdida": {str(a): metricas.pct_perdida(p, a) for a in PLAZOS},
                      "escenarios": {str(a): metricas.escenarios(p, ipc_r, a) for a in PLAZOS}}
                en_grafico = inst.get("grafico") or (inst.get("destacado") and
                                                     not any(i.get("grafico") for i in set_[g["id"]]))
                if en_grafico:
                    grafico["series"].append({"grupo": g["id"], "valores": metricas.crecimiento(p)})
            out.append(d)
        grupos.append({**g, "instrumentos": out})

    return {"vista": clave, "moneda": moneda, "simbolo": v["simbolo"], "inflacion_nombre": v["inflacion_nombre"],
            "datos_al": str(ipc_r.index[-1]), "desde": config["desde"], "inflacion_interanual": infl,
            "grupos": grupos, "grafico": grafico}, []


def _tickers_declarados(config: dict) -> dict[str, str]:
    """Cada ticker de Yahoo de la configuración con la moneda en la que dice que cotiza."""
    out = {}
    for grupos in config["sets"].values():
        for insts in grupos.values():
            for i in insts:
                if i.get("yahoo"):
                    out[i["yahoo"]] = i["moneda_cotiza"]
                for p in i.get("proxy") or []:
                    if "yahoo" in p:
                        out[p["yahoo"]] = p["moneda_cotiza"]
                    for c in p.get("mezcla", []):
                        out[c["yahoo"]] = p["moneda_cotiza"]
    return out


def chequear_monedas(config: dict, moneda_de: Callable[[str], str | None]) -> list[str]:
    """Compara la moneda declarada con la que reporta la fuente. Si se declara mal, la conversión sale al revés."""
    errores = []
    for t, declarada in _tickers_declarados(config).items():
        real = moneda_de(t)
        if real and real.upper() != declarada:
            errores.append(f"{t}: la configuración dice que cotiza en {declarada}, pero la fuente dice {real}")
    return errores


def construir(config: dict, obtener: Callable[[str], pd.Series],
              moneda_de: Callable[[str], str | None] | None = None) -> dict[str, dict]:
    if moneda_de:
        errores_moneda = chequear_monedas(config, moneda_de)
        if errores_moneda:
            raise ValueError("Monedas mal declaradas, no se publica nada:\n" + "\n".join(errores_moneda))
    salida, errores = {}, []
    for clave in config["vistas"]:
        vista, e = _vista(clave, config, obtener)
        errores += e
        salida[clave] = vista
    if errores:
        raise ValueError("Series inválidas, no se publica nada:\n" + "\n".join(errores))
    return salida


def _obtener_real() -> Callable[[str], pd.Series]:
    cache: dict[str, pd.Series] = {}
    bajadores = {"yahoo": fuentes.bajar_yahoo, "hicp": fuentes.bajar_hicp,
                 "fred": fuentes.bajar_fred, "bce": fuentes.bajar_bce, "bbk": fuentes.bajar_bbk}

    def obtener(nombre: str) -> pd.Series:
        if nombre not in cache:
            tipo, arg = nombre.split(":", 1)
            seguro = nombre.replace("/", "_").replace(":", "_").replace("^", "_")
            cache[nombre] = fuentes.actualizar(seguro, lambda: bajadores[tipo](arg))
        return cache[nombre]

    return obtener


def main() -> int:
    with open("config/instrumentos.yaml") as fh:
        config = yaml.safe_load(fh)
    try:
        salida = construir(config, _obtener_real(), fuentes.moneda_yahoo)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    dir_ = Path("site/data")
    dir_.mkdir(parents=True, exist_ok=True)
    for clave, vista in salida.items():
        (dir_ / f"{clave}.json").write_text(json.dumps(vista, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: datos al {salida['es']['datos_al']} en {', '.join(salida)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
