import pandas as pd
import pytest

from ahorro import fuentes as f


def serie(vals, inicio="2010-01"):
    return pd.Series(list(vals), index=pd.period_range(inicio, periods=len(vals), freq="M"), dtype=float)


def test_actualizar_guarda_y_combina(tmp_path):
    f.actualizar("x", lambda: serie([1, 2, 3]), tmp_path)
    out = f.actualizar("x", lambda: serie([30, 4], inicio="2010-03"), tmp_path)
    assert list(out) == [1, 2, 30, 4]
    assert (tmp_path / "x.csv").read_text().startswith("mes,valor\n2010-01,")


def test_actualizar_usa_cache_si_falla(tmp_path, capsys):
    f.actualizar("x", lambda: serie([1, 2]), tmp_path)

    def roto():
        raise TimeoutError("yahoo")

    assert list(f.actualizar("x", roto, tmp_path)) == [1, 2]
    assert "AVISO: x sin actualizar" in capsys.readouterr().err


def test_actualizar_sin_cache_propaga(tmp_path):
    def roto():
        raise TimeoutError("yahoo")

    with pytest.raises(TimeoutError):
        f.actualizar("x", roto, tmp_path)


def test_actualizar_serie_vacia_cuenta_como_falla(tmp_path, capsys):
    f.actualizar("x", lambda: serie([1, 2]), tmp_path)
    assert list(f.actualizar("x", lambda: serie([]), tmp_path)) == [1, 2]
    assert "AVISO" in capsys.readouterr().err


def test_mensual_promedia_diarias():
    idx = pd.to_datetime(["2020-01-02", "2020-01-31", "2020-02-03"])
    out = f.mensual(pd.Series([1.0, 3.0, 5.0], index=idx), "promedio")
    assert list(out) == [2.0, 5.0] and str(out.index[0]) == "2020-01"


def test_mensual_ultimo_valor():
    idx = pd.to_datetime(["2020-01-02", "2020-01-31"])
    assert list(f.mensual(pd.Series([1.0, 3.0], index=idx), "ultimo")) == [3.0]


def test_actualizar_descarta_el_mes_en_curso(tmp_path):
    ahora = pd.Period.now("M")
    s = pd.Series([1.0, 2.0, 3.0], index=pd.period_range(ahora - 2, periods=3, freq="M"))
    out = f.actualizar("x", lambda: s, tmp_path)
    assert out.index[-1] == ahora - 1
    assert str(ahora) not in (tmp_path / "x.csv").read_text()


def test_parse_bbk():
    texto = ('"",BBSIS.M.X,BBSIS.M.X_FLAGS\n"",Titulo largo,\nBBK_UNIT_ENG,percent,\nDecimals,2,\n'
             'last update,2026-10-01,\n1972-09,6.26,\n1972-10,.,\n1972-11,7.88,\n')
    out = f.parse_bbk(texto)
    assert list(out) == [6.26, 7.88] and str(out.index[0]) == "1972-09"
