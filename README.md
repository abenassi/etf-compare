# ¿Dónde pongo mis ahorros?

Página estática, pensada para el celular, que ayuda a elegir dónde poner los ahorros según cuándo se va a necesitar la plata:

- liquidez;
- mediano plazo (1 a 5 años);
- jubilación.

Compara cada ETF contra la inflación de España, de la zona euro o de EE.UU.

- Diseño: `docs/superpowers/specs/2026-10-19-ahorro-design.md`
- Plan: `docs/superpowers/plans/2026-10-19-ahorro.md`

## Correr el pipeline

```
uv sync
uv run pytest
uv run python -m ahorro.build
```
