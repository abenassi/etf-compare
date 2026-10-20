# ¿Dónde pongo mis ahorros?

Página estática, pensada para el celular, que ayuda a elegir dónde poner los ahorros según cuándo se va a necesitar la plata:

- liquidez;
- mediano plazo (1 a 5 años);
- jubilación.

Muestra cada ETF en euros o en dólares, convertido a la moneda elegida.

- Diseño: `docs/superpowers/specs/2026-10-19-ahorro-design.md`
- Plan: `docs/superpowers/plans/2026-10-19-ahorro.md`

## Correr el pipeline

```
uv sync
uv run pytest
uv run python -m ahorro.build
```

## Dónde está

https://abenassi.github.io/etf-compare/. Se puede preseleccionar la vista con `?pais=eur` o `?pais=usd`.

La Action `actualizar.yml` corre el día 20 de cada mes (también se puede disparar a mano desde Actions):

1. Corre los tests.
2. Baja los datos y recalcula.
3. Comitea `data/` y `site/data/`.
4. Publica en Pages.

Si alguna serie tiene un salto raro, la Action falla y no se publica nada; queda online la versión anterior.

## Mantenimiento

- **Cambiar un ETF:** editar `config/instrumentos.yaml`. El destacado es el que tiene `destacado: true`; con proxy se
  completa la historia anterior al lanzamiento del fondo.
- **Rendimiento al vencimiento de los bonos** (el número de "Hoy"): se carga a mano en `hoy.ytm` y `hoy.fecha` de cada
  bono. Se saca de la ficha del emisor (iShares: "Weighted Average YTM"; Vanguard: "Yield to maturity"). Conviene
  revisarlo cada 2 o 3 meses. La página muestra la fecha del dato.
- **Tabla de bonos con vencimiento (iBonds):** en `config/instrumentos.yaml`, el ítem `tipo: escalera` tiene un `ytm`
  por año (el "Weighted Average YTM" bruto de cada ficha de iShares) y una `fecha`. Se actualiza a mano junto con los
  demás. Cuando un año vence, se saca de la lista y se agrega el siguiente.
- La cuenta remunerada se modela con €STR (o la letra del Tesoro a 3 meses en la vista dólar) menos 0,5 puntos, con piso
  de 0%. Los parámetros están en `cuenta:` de la configuración.
