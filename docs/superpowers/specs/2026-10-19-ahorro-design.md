# ¿Dónde pongo mis ahorros? Diseño

Fecha: 2026-10-19. Repo: `abenassi/etf-compare` (se reusa; el código viejo de Streamlit se borra entero).
Mockup de referencia, con números inventados: [`docs/mockup/index.html`](../../mockup/index.html).

## Intención

A Agustín le preguntan seguido en qué invertir; el disparador fue su hermana en Barcelona, con un horizonte de 1 a 4 años
(por ejemplo, para comprar un departamento). Quiere un link listo para mandar que la persona abra **sola, en el celular**, y
entienda sin que nadie le explique:

1. Que un ahorro rinde de verdad solo si le gana a la inflación de su moneda.
2. Que más rendimiento no siempre es mejor: la volatilidad decide para qué plazo sirve cada instrumento. Las acciones no
   sirven para la plata del depto en 3 años, porque justo ese año el mercado puede estar abajo.

Y que, entendido eso, sepa qué ETF concreto usar en cada caso: la página **recomienda**, no solo compara.

## Objetivos

- Una sola página estática, mobile-first, en español, limpia y directa.
- Tres grupos de ahorro, siempre visibles los tres, en este orden:
  1. **Liquidez** (emergencias, gastos de los próximos meses).
  2. **Mediano plazo** (1 a 5 años, un objetivo concreto).
  3. **Jubilación** (10 años o más).
- En cada grupo, un instrumento destacado (etiqueta "Recomendado") y 1 o 2 alternativas.
- Selector de moneda e inflación arriba: Euro · inflación España (por defecto), Euro · zona euro, Dólar · inflación EE.UU.
  Se puede preseleccionar por link (`?pais=es|ea|us`).
- Datos reales que se actualizan solos una vez por mes.
- Publicada en GitHub Pages desde este repo (es público).

## No objetivos

- No es una calculadora personalizada: no se carga monto, edad ni perfil.
- No hay una página por persona ni notas personalizadas.
- No hay login, backend ni base de datos.
- No cubre impuestos en detalle, más allá de una nota corta.
- No muestra métricas técnicas (Sharpe, desvío estándar, beta, drawdown con ese nombre).

## Antiobjetivos (sería un fracaso aunque funcione)

- Que alguien sin formación financiera no la entienda en el celular sin ayuda.
- Que prometa que algo le gana a la inflación cuando hoy no es así (ver "Hoy").
- Que muestre números rotos por datos malos de la fuente (saltos de split, meses faltantes).
- Que haya que mantenerla a mano todos los meses.

## Qué ve la persona (decidido con Agustín, sobre el mockup)

De arriba a abajo:

1. **Título y bajada:** "¿Dónde pongo mis ahorros?" / "Una guía corta para elegir según cuándo vas a necesitar la plata".
2. **Selector de moneda** (chips).
3. **Tres tarjetas de grupo**, con el color del grupo. Cada una tiene un título, para qué sirve en una línea y sus
   instrumentos. Por instrumento:
   - Nombre en castellano llano, más ticker y nombre del fondo en chico. Al destacado lo acompaña la etiqueta "el que yo
     usaría".
   - **Rendimiento por año sobre la inflación** (verde si es positivo, rojo si es negativo).
   - **Tabla "perdiste plata"**: si lo tenías 1, 3, 5 o 10 años, en qué porcentaje de los casos terminaste con menos
     plata (nominal, en la moneda elegida) de la que pusiste. Un 0% se muestra como "nunca". El color va de neutro a
     rojo, más oscuro cuanto más riesgo.
   - **Al tocar el instrumento se despliega "Si ponías 10.000 y los sacabas a los…"**, con un selector de plazo (1, 3, 5
     o 10 años) y tres filas: Peor, Típico y Mejor, en moneda de hoy (descontada la inflación). Son barras desde una raya
     que marca los 10.000. **La escala es la misma para todos los instrumentos**, para que se vea a simple vista que las
     acciones se mueven mucho y los bonos poco.
   - **"Hoy"** (solo liquidez y bonos): lo que rinde hoy (rendimiento al vencimiento, o la tasa actual en el monetario)
     contra la inflación actual. Va acompañado de una nota honesta cuando queda por debajo, por ejemplo: "hoy la inflación
     está alta: esto protege la mayor parte de tu plata, no toda". Para el mediano plazo el mensaje es perder lo menos
     posible sin arriesgar, no "ganarle seguro a la inflación".
4. **Gráfico "10.000€ en los últimos 10 años"**: una línea por grupo (su instrumento destacado), más la inflación en
   punteado gris como "lo que necesitabas para no perder". Las etiquetas van directamente al final de cada línea, con el
   valor final. Lleva un texto corto: las acciones terminaron más arriba, pero en el camino bajaron fuerte.
5. **Pie:** fecha de los datos, "se actualiza cada mes", "rendimientos ya descontadas las comisiones", "antes de que
   existiera cada ETF se usa el índice que replica", una nota fiscal de España (ver abajo) y un aviso legal
   completo. Arriba de todo va una barra corta: "Información educativa, no es asesoramiento financiero", con link al aviso.
   El rendimiento de cada instrumento se muestra nominal anual y, entre paréntesis, contra la inflación (pedido de Agustín
   el 2026-10-19).

Lo que Agustín sacó del mockup y no vuelve: el recuadro de "10.000€ en el colchón desde 2020" y el selector "¿cuándo vas a
necesitar la plata?" que resaltaba un grupo.

## Instrumentos (vista euro)

Todos son UCITS y se compran desde brokers españoles. Surgen de la investigación del 2026-10-19 (justETF, iShares, BCE).

| Grupo | Destacado | Alternativas |
|---|---|---|
| Liquidez | Cuenta remunerada (tasa de referencia, sin ticker) | **XEON**, Xtrackers II EUR Overnight Rate Swap 1C, LU0290358497, `XEON.DE`, desde 2007 |
| Mediano plazo | **XZE5**, Xtrackers EUR Corp Bond Short Duration SRI PAB 1C, LU2178481649, `XZE5.DE`, acumula, desde 2020-07 | **IVOA**, iShares iBonds Dec 2028 Term € Corp Acc, IE0008UEVOE0, `IVOA.DE` (vencimiento fijo, ideal si el objetivo cae en 2028); **IBCA**, iShares € Govt Bond 1-3yr, IE00B14X4Q57, `IBCA.DE` (soberanos, sin riesgo de crédito) |
| Jubilación | **VWCE**, Vanguard FTSE All-World Acc, IE00BK5BQT80, `VWCE.DE` | **EUNL/IWDA**, iShares Core MSCI World, IE00B4L5Y983, `EUNL.DE`; **CSPX**, iShares Core S&P 500, IE00B5BMR087, `CSPX.AS`; **CNDX**, iShares Nasdaq 100, IE00B53SZB19, `CNDX.AS`, presentado como "más riesgo" |

Mi decisión, que Agustín puede cambiar: en Liquidez el destacado es la cuenta remunerada y XEON es la alternativa, porque
Agustín dijo que en ese grupo "la mayoría de las veces va a ser una cuenta remunerada". La cuenta remunerada no tiene serie
de precios: se modela con €STR menos 0,5 puntos (ajustable en la configuración), **con piso de 0%** (decidido con
Agustín: entre 2014 y 2022 las tasas fueron negativas, pero los bancos no se las cobraban al ahorrista minorista), y se
rotula como aproximación. XEON se muestra tal cual, incluidas sus pérdidas chicas de esos años.

**IVOA (mi decisión):** como vence en dic-2028, no lleva tabla de plazos ni escenarios. Solo muestra "Hoy": lo que
rinde si lo tenés hasta el vencimiento, contra la inflación actual, y la fecha de vencimiento.

La lista vive en un archivo de configuración (`instrumentos.yaml` o similar), no en el código. Cambiar un ETF tiene que
ser editar ese archivo y nada más.

**Vista dólar (mi decisión):** usa ETFs listados en EE.UU., porque quien ahorra en dólares (residente en EE.UU., o un
argentino con broker en EE.UU.) compra esos y no UCITS cubiertos a euro. Propuesta:
- Liquidez: el destacado es la cuenta remunerada, modelada con la letra del Tesoro a 3 meses (FRED `TB3MS`) menos
  0,5 puntos, con piso de 0%; la alternativa es `BIL` (desde 2007).
- Mediano plazo: `VCSH` (destacado, desde 2009-11) e `IGSB`.
- Jubilación: `VT` (destacado, desde 2008), `VOO` (completado con `^SP500TR`) y `QQQ`.

El builder puede ajustar la lista verificando tamaño y comisión, siempre que todos tengan datos en el período común.

## Datos

- **Precios:** Yahoo Finance vía `yfinance`, mensuales, con `auto_adjust=True` (incluye dividendos). Verificado: hay
  historia mensual de todos los tickers de la tabla.
- **Extender la historia hacia atrás hasta 2000-01 (decidido con Agustín):** antes de que exista el ETF, se empalma su proxy, se
  convierte a la moneda de la vista y se le descuenta el TER. Proxies verificados:
  - VWCE: ACWI (desde 2008).
  - EUNL: URTH, y antes ACWI.
  - CSPX: `^SP500TR` (desde 1988).
  - CNDX: QQQ (desde 1999).
  - XZE5: EUNT, iShares € Corp Bond 1-5yr, `EUNT.DE` (desde 2009-12), menos la diferencia de TER.
  - XEON tiene datos reales desde 2008. €STR (`EST/B.EU000A2X2A25.WT`, desde 2019-10) y EONIA antes (`EON/D.EONIA_TO.RATE`)
    sirven para modelar la cuenta remunerada.
  - El tipo de cambio EUR/USD sale del BCE (`EXR/M.USD.EUR.SP00.E`, desde 1999). Yahoo `EURUSD=X` arranca recién en 2003.

  La página aclara desde cuándo es dato real de cada ETF.
- **Inflación:**
  - España y zona euro: Eurostat `prc_hicp_minr`, `coicop18=TOTAL`, `unit=I15`, `geo=ES` y `geo=EA` (mi decisión: EA,
    la composición oficial que va cambiando).
  - EE.UU.: FRED `fredgraph.csv?id=CPIAUCSL`, sin clave.
  - Ojo: `prc_hicp_midx` (la tabla vieja) está congelada en 2025-12 y no hay que usarla. La serie ICP del BCE también.
- **Datos malos conocidos en Yahoo:**
  - `SPYI.DE` tiene un salto de −96% en 2015.
  - `SXR8.DE` tiene meses erróneos en 2010 (por eso CSPX se toma de `CSPX.AS`).
  - `VUAA.DE` arranca recién en 2024-12.

  Toda serie pasa por una validación: un salto mensual de más del 15% en bonos o liquidez, o de más del 35% en acciones,
  frena la publicación y deja la versión anterior online. Los umbrales los fija el builder.
- **Robustez:** Yahoo no es una API oficial y puede bloquear runners de GitHub. Los CSV crudos se guardan en el repo y la
  corrida mensual solo agrega lo nuevo. Si una fuente falla, se publica igual con los datos del mes anterior y la fecha
  correcta; nunca con huecos.
- **"Hoy":** hace falta el rendimiento al vencimiento de cada ETF de bonos y la tasa de referencia de la cuenta
  remunerada. Preferencia: que lo baje la corrida mensual desde la ficha del emisor. Si eso resulta frágil, va un valor a
  mano en la configuración con su fecha, y la página muestra esa fecha. Lo decide el builder.

## Cálculos (definiciones)

Todo se calcula con datos mensuales, en la moneda de la vista, sobre un **período común para todos los instrumentos y
vistas: desde 2000-01 hasta el último mes disponible**. Primero fue 2010-01. El 2026-10-19 Agustín lo extendió a 2000:
con 2010-2026 las acciones daban "nunca perdiste plata a 3 años", y eso contradecía la lección. El período incluye
2000-2002, 2008, la crisis del euro, el Covid y 2022.

Proxies largos:
- acciones del mundo: mezcla 60/40 de VTSMX y VGTSX;
- `^SP500TR` y QQQ;
- bonos en dólares: VFSTX;
- bonos en euros antes de 2009: un bono sintético armado con la tasa alemana a 2 años del Bundesbank;
- monetarios: EONIA y T-bill.

La línea de Liquidez del gráfico es el fondo monetario (XEON o BIL), no la cuenta modelada.

- **Rendimiento por año sobre la inflación:** rendimiento anualizado de los últimos 10 años, ya deflactado por la inflación
  de la vista: `(1+nominal)/(1+inflación) − 1`, anualizado. Mi decisión: 10 años, para que coincida con el gráfico.
- **"Perdiste plata" a N años:** sobre todas las ventanas móviles de N años que arrancan a principio de cada mes, el
  porcentaje en que el valor final nominal quedó por debajo del inicial.
- **Escenarios de 10.000 a N años:** sobre las mismas ventanas móviles, el valor final deflactado. Peor = el mínimo
  observado; Típico = la mediana; Mejor = el máximo observado. Mi decisión: usar el peor que realmente pasó y no un
  percentil, porque "lo peor que pasó" se explica solo.
- **Gráfico de 10 años:** el valor de 10.000 en los últimos 120 meses para el destacado de cada grupo, más la inflación
  acumulada.
- **"Hoy":** rendimiento al vencimiento (o tasa) menos la inflación interanual del último mes.

## Nota fiscal (España, texto corto en el pie)

- En España los ETF no se traspasan sin tributar, a diferencia de los fondos indexados: cada venta paga impuesto (19 a 30%).
- Por eso se eligieron ETFs de acumulación, que difieren el impuesto hasta la venta.
- Si la plata está en un broker extranjero y supera los 50.000€, hay que mirar el Modelo 720.

## Cómo se construye

- **Repo:** `abenassi/etf-compare`. Se borra todo lo viejo (Streamlit, scraper de lazyportfolioetf, Replit, Poetry). Se
  puede renombrar el repo más adelante.
- **Generación de datos:** un script de Python (`python`, con `uv`) que baja, valida, calcula y escribe un JSON por vista.
  Más tests de los cálculos con series sintéticas, para que las definiciones de arriba queden fijadas.
- **Página:** HTML, CSS y JS estáticos, sin framework ni build step. Lee el JSON. Los gráficos son SVG a mano o con una
  librería liviana. Tiene que pasar las reglas de accesibilidad de color (un solo tono por magnitud, etiquetas directas,
  texto en tinta y no en el color de la serie).
- **Automatización:** una GitHub Action mensual (y manual con `workflow_dispatch`) corre el script, comitea CSV y JSON si
  la validación pasó, y publica en Pages. La URL queda `abenassi.github.io/etf-compare/`.
- **Entrega:** está terminado cuando la página está publicada en Pages con datos reales, la Action mensual corrió al
  menos una vez de punta a punta y la página se revisó en un viewport de celular (390 px) en las tres vistas.

## Queda a criterio del builder

- La estructura de archivos, la librería de gráficos (o ninguna) y el formato exacto del JSON.
- Los textos finales, respetando el tono: castellano neutro rioplatense-friendly, frases cortas, sin jerga.
- Los umbrales exactos de la validación.
- Cómo conseguir el rendimiento al vencimiento (automático o manual con fecha).
- El ajuste fino de la lista de la vista dólar.
