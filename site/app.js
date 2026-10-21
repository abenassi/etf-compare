// Renderiza la página a partir de data/{vista}.json (lo genera ahorro/build.py).
const VISTAS = ["eur", "usd"];
const ALIAS = { es: "eur", ea: "eur", us: "usd" }; // links viejos con ?pais=es|ea|us
const COLOR = { liq: "#1baf7a", med: "#2a78d6", jub: "#eb6834" };
const GRIS = "#8a8983";
const PLAZOS = ["1", "3", "5", "10"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];

let datos = null;

const pct = (x, signo = false) =>
  (signo && x >= 0 ? "+" : "") + (x * 100).toLocaleString("es-ES", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
const plata = v => Math.round(v).toLocaleString("es-ES") + " " + datos.simbolo;
const mes = p => { const [a, m] = p.split("-"); return `${MESES[+m - 1]} de ${a}`; };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function vistaDeUrl() {
  const p = new URLSearchParams(location.search).get("pais");
  const v = ALIAS[p] || p;
  return VISTAS.includes(v) ? v : "eur";
}

// Celda "perdiste plata": un solo tono, más oscuro = más veces perdiste.
function celda(p) {
  if (p === null || p === undefined) return `<td style="background:#f3f2ee;color:${GRIS}" title="sin datos suficientes">–</td>`;
  const pasos = ["#f3f2ee", "#fbd9c9", "#f6b294", "#ee8a5f", "#d4582b", "#a83d17"];
  const pc = p === 0 ? 0 : Math.max(1, Math.round(p * 100)); // "nunca" solo si de verdad nunca pasó
  const i = pc === 0 ? 0 : Math.min(5, 1 + Math.floor(pc / 7));
  return `<td style="background:${pasos[i]};color:${i >= 4 ? "#fff" : "#0b0b0b"}" title="${pc}% de las veces terminaste con menos de lo que pusiste">${pc === 0 ? "nunca" : pc + "%"}</td>`;
}

// Escala común a todos los instrumentos para un mismo plazo, para que se compare a simple vista.
function escala(plazo) {
  let min = 10000, max = 10000;
  for (const g of datos.grupos) for (const i of g.instrumentos) {
    const e = (i.escenarios || {})[plazo];
    if (!e) continue;
    min = Math.min(min, e.peor); max = Math.max(max, e.mejor);
  }
  return { min: min * 0.97, max: max * 1.02 };
}

function escenarios(inst, plazo, color, sc) {
  const e = inst.escenarios[plazo];
  if (!e) return `<div class="nota">Todavía no hay suficiente historia para este plazo.</div>`;
  const pos = v => ((v - sc.min) / (sc.max - sc.min) * 100).toFixed(1) + "%";
  const fila = (lbl, v) => {
    const a = Math.min(v, 10000), b = Math.max(v, 10000);
    return `<div class="esc"><span class="lbl">${lbl}</span>
      <div class="bar" style="--b:${pos(10000)}"><div class="fill" style="left:${pos(a)};width:calc(${pos(b)} - ${pos(a)});background:${color};opacity:${lbl === "Típico" ? 1 : .55}"></div><div class="base"></div></div>
      <span class="val" style="color:${v < 10000 ? "var(--bad)" : "var(--text)"}">${plata(v)}</span></div>`;
  };
  return fila("Peor", e.peor) + fila("Típico", e.tipico) + fila("Mejor", e.mejor);
}

// En Liquidez y Mediano plazo lo que importa es la tasa de hoy: pasa a ser el número grande y el promedio de 10 años
// queda de contexto (es más bajo por los años de tasas en cero o negativas).
const hoyPrincipal = (g, inst) => (g.id === "liq" || g.id === "med") && inst.hoy && inst.rend_anual !== null;
const POR_QUE_PROMEDIO = {
  liq: "más bajo porque entre 2016 y 2022 las tasas estuvieron en cero o negativas",
  med: "más bajo porque entre 2016 y 2022 las tasas estuvieron en cero o negativas, y en 2022 los bonos cayeron cuando subieron",
};

function hoy(h, inst, principal = false) {
  if (!h) return "";
  const que = inst.sin_plazos ? `Si lo tenés hasta ${esc(inst.vence)}, rinde` : "Con las tasas de hoy rinde";
  const fuente = h.fuente ? `Dato de referencia: ${esc(h.fuente)}, al ${esc(h.fecha)}.` : `Dato al ${esc(h.fecha)}.`;
  if (principal) return `<div class="hoy"><span class="nota" style="margin-top:0">${fuente}</span></div>`;
  return `<div class="hoy">${que} <b>${pct(h.rinde)}</b> por año.<span class="nota">${fuente}</span></div>`;
}

function instrumento(g, inst, j) {
  const principal = hoyPrincipal(g, inst);
  const n = principal ? inst.hoy.rinde : inst.rend_anual;
  const etiqueta = !principal ? "promedio por año de los últimos 10 años"
    : g.id === "med" ? "por año con las tasas de hoy, ya descontada la comisión" : "por año, con las tasas de hoy";
  const cabeza = `<div class="row"><span class="name">${esc(inst.nombre)}${inst.destacado ? "<em>recomendado</em>" : ""}</span>
      ${n === null ? "" : `<span class="real ${n >= 0 ? "pos" : "neg"}">${pct(n, true)}</span>`}</div>
    <div class="row"><span class="tick">${esc(inst.detalle)}</span>${n === null ? "" : `<span class="sub">${etiqueta}</span>`}</div>
    ${principal ? `<div class="sub">Promedio de los últimos 10 años: ${pct(inst.rend_anual, true)}, ${POR_QUE_PROMEDIO[g.id]}.</div>` : ""}
    ${!inst.sin_plazos && inst.real_desde && inst.real_desde > datos.desde ? `<div class="sub">Dato real del fondo desde ${esc(inst.real_desde.slice(0, 4))}; antes, ${esc(inst.antes)}.</div>` : ""}`;
  if (inst.escalera) {
    return `<div class="inst" style="cursor:default">${cabeza}
      <div class="hoy">Funciona parecido a un plazo fijo: cada fondo tiene bonos de cientos de empresas que vencen el mismo año. En diciembre de ese año el fondo se cierra solo y te deposita la plata en la cuenta del broker. Si lo tenés hasta el final, sabés casi exacto cuánto te da. Elegí el año en que vas a necesitar la plata, o repartí entre dos o tres años.
        <span class="nota">No tiene la garantía de depósitos de hasta 100.000 €, pero está repartido en cientos de empresas. Si lo vendés antes, cobrás el precio de ese día.</span></div>
      <table class="chances escalera"><tr><th style="text-align:left">Vence en diciembre de</th><th>ETF</th><th>Rinde por año si lo tenés hasta el final</th></tr>
        ${inst.escalera.map(f => `<tr><td style="text-align:left">${f.vence}</td><td>${esc(f.ticker)}</td><td><b>${pct(f.neto)}</b></td></tr>`).join("")}</table>
      <div class="nota">Rendimiento al vencimiento de la ficha de iShares al ${esc(inst.fecha)}, ya descontada la comisión (0,12%). No está garantizado: si alguna empresa no paga, rinde menos.</div></div>`;
  }
  if (inst.sin_plazos) {
    return `<div class="inst" style="cursor:default">${cabeza}${hoy(inst.hoy, inst)}
      <div class="nota">Es un bono con fecha de vencimiento: si lo tenés hasta ${esc(inst.vence)}, sabés casi exacto cuánto te da.</div></div>`;
  }
  return `<div class="inst" data-g="${g.id}" data-j="${j}">${cabeza}${hoy(inst.hoy, inst, principal)}
    <table class="chances"><tr><th>Si lo tenías…</th>${PLAZOS.map(p => `<th>${p} ${p === "1" ? "año" : "años"}</th>`).join("")}</tr>
      <tr><th style="text-align:left">perdiste plata</th>${PLAZOS.map(p => celda(inst.perdida[p])).join("")}</tr></table>
    <div class="tap">Tocá para ver qué pasaba con 10.000 ${esc(datos.simbolo)} ▾</div>
    <div class="detalle">
      <b style="font-size:14px">Si ponías 10.000 ${esc(datos.simbolo)} y los sacabas a los…</b>
      <div class="plazos">${PLAZOS.map(p => `<button class="chip ${p === "3" ? "on" : ""}" data-p="${p}">${p} ${p === "1" ? "año" : "años"}</button>`).join("")}</div>
      <div class="escs">${escenarios(inst, "3", COLOR[g.id], escala("3"))}</div>
      <div class="nota">En ${datos.moneda === "EUR" ? "euros" : "dólares"}. La raya negra marca los 10.000 que pusiste; la escala es la misma para todos los instrumentos. Peor y mejor son lo peor y lo mejor que pasó desde ${mes(datos.desde)}.</div>
    </div></div>`;
}

function grupos() {
  document.getElementById("grupos").innerHTML = datos.grupos.map(g => `
    <section class="grupo" style="--k:${COLOR[g.id]}">
      <div class="tag"><i></i>${esc(g.tag)}</div>
      <h3>${esc(g.titulo)}</h3>
      <div class="para">${esc(g.para)}</div>
      ${g.instrumentos.map((x, j) => instrumento(g, x, j)).join("")}
    </section>`).join("");
}

const k = v => (v / 1000).toLocaleString("es-ES", { maximumFractionDigits: 1 }) + "k";
const nombreGrupo = id => datos.grupos.find(g => g.id === id).tag;
const leyenda = ids => ids.map(id => `<span><i style="background:${COLOR[id]}"></i>${esc(nombreGrupo(id))}</span>`).join("");

// Embudo: resultado de 10.000 según cuántos años los tuviste (peor, típico y mejor desde el inicio de los datos).
function embudo() {
  const e = datos.embudo, P = e.plazos, n = P.length - 1;
  const tope = Math.max(...e.series.flatMap(s => s.tipico)) * 1.5;
  const piso = Math.min(...e.series.flatMap(s => s.peor)) * 0.9;
  const X = i => 34 + i / n * 286, Y = v => 205 - (Math.min(v, tope) - piso) / (tope - piso) * 195;
  const linea = (vals) => vals.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  let svg = "";
  const paso = tope - piso > 20000 ? 10000 : 5000;
  for (let t = Math.ceil(piso / paso) * paso; t < tope; t += paso)
    svg += `<line x1="34" x2="320" y1="${Y(t)}" y2="${Y(t)}" stroke="#e6e5e0"/><text x="0" y="${Y(t) + 3}" font-size="10" fill="${GRIS}">${k(t)}</text>`;
  for (const s of e.series) {
    const banda = linea(s.mejor) + s.peor.map((v, i) => `L${X(n - i).toFixed(1)},${Y(s.peor[n - i]).toFixed(1)}`).join("") + "Z";
    svg += `<path d="${banda}" fill="${COLOR[s.grupo]}" fill-opacity="${s.grupo === "jub" ? 0.16 : 0.28}" stroke="none"/>`;
  }
  svg += `<line x1="34" x2="320" y1="${Y(10000)}" y2="${Y(10000)}" stroke="#0b0b0b" stroke-width="1.2" stroke-dasharray="4 3"/>`;
  svg += `<text x="36" y="${Y(10000) - 4}" font-size="10" fill="#0b0b0b">lo que pusiste</text>`;
  for (const s of e.series) svg += `<path d="${linea(s.tipico)}" fill="none" stroke="${COLOR[s.grupo]}" stroke-width="2.2"/>`;
  const jub = e.series.find(s => s.grupo === "jub");
  if (jub) {
    svg += `<circle cx="${X(0)}" cy="${Y(jub.peor[0])}" r="3.5" fill="${COLOR.jub}" stroke="#fff" stroke-width="1.5"/>`;
    svg += `<text x="${X(0) + 6}" y="${Y(jub.peor[0]) + 4}" font-size="10" fill="#52514e">peor a 1 año: ${plata(jub.peor[0])}</text>`;
    svg += `<text x="${X(n)}" y="${Y(jub.tipico[n]) - 6}" font-size="10" fill="#0b0b0b" text-anchor="end"><tspan font-weight="700">${plata(jub.tipico[n])}</tspan> típico a ${P[n]} años</text>`;
  }
  for (const i of [0, 4, 9, 14].filter(i => i <= n))
    svg += `<text x="${X(i)}" y="222" font-size="10" fill="${GRIS}" text-anchor="middle">${P[i]} ${P[i] === 1 ? "año" : "años"}</text>`;
  document.getElementById("embudo").innerHTML = svg;
  document.getElementById("leyenda-embudo").innerHTML = leyenda(e.series.map(s => s.grupo)) +
    `<span>banda: de lo peor a lo mejor</span>`;
  const cols = [0, 2, 4, 9, 14].filter(i => i <= n);
  document.getElementById("pierde").innerHTML =
    `<tr><th style="text-align:left">Perdiste plata…</th>${cols.map(i => `<th>${P[i]} ${P[i] === 1 ? "año" : "años"}</th>`).join("")}</tr>` +
    e.series.map(s => `<tr><th style="text-align:left">${esc(nombreGrupo(s.grupo))}</th>${cols.map(i => celda(s.pierde[i])).join("")}</tr>`).join("");
}

// Historia real desde el primer mes de datos.
function grafico() {
  const gr = datos.historia, N = gr.meses.length - 1;
  const todas = gr.series.flatMap(s => s.valores);
  const lo = Math.min(...todas) * 0.92, hi = Math.max(...todas) * 1.04;
  const X = i => 34 + i / N * 196, Y = v => 200 - (v - lo) / (hi - lo) * 185;
  const camino = d => d.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  let svg = "";
  const paso = hi - lo > 30000 ? 20000 : hi - lo > 15000 ? 10000 : 5000;
  for (let t = Math.ceil(lo / paso) * paso; t < hi; t += paso)
    svg += `<line x1="34" x2="230" y1="${Y(t)}" y2="${Y(t)}" stroke="#e6e5e0"/><text x="0" y="${Y(t) + 3}" font-size="10" fill="${GRIS}">${k(t)}</text>`;
  svg += `<line x1="34" x2="230" y1="${Y(10000)}" y2="${Y(10000)}" stroke="#0b0b0b" stroke-width="1" stroke-dasharray="2 3"/>`;
  for (const s of gr.series)
    svg += `<path d="${camino(s.valores)}" fill="none" stroke="${COLOR[s.grupo]}" stroke-width="1.8" stroke-linejoin="round"/>`;
  const finales = gr.series.map(s => ({ v: s.valores[N], t: nombreGrupo(s.grupo) }))
    .sort((a, b) => a.v - b.v);
  let prev = 999; // de abajo hacia arriba, separadas para que no se pisen
  for (const f of finales) {
    const y = Math.min(Y(f.v) + 3, prev - 12); prev = y;
    svg += `<text x="235" y="${y}" font-size="10" fill="#0b0b0b"><tspan font-weight="700">${k(f.v)}</tspan> <tspan fill="#52514e">${esc(f.t)}</tspan></text>`;
  }
  const jub = gr.series.find(s => s.grupo === "jub");
  if (jub) {
    const v = jub.valores, iMin = v.indexOf(Math.min(...v));
    let iVuelve = -1;
    for (let i = N; i >= 0; i--) if (v[i] < 10000) { iVuelve = i + 1; break; }
    svg += `<circle cx="${X(iMin)}" cy="${Y(v[iMin])}" r="3.5" fill="${COLOR.jub}" stroke="#fff" stroke-width="1.5"/>`;
    svg += `<text x="${X(iMin) + 6}" y="${Y(v[iMin]) - 2}" font-size="10" fill="#52514e">${pct(v[iMin] / 10000 - 1)} en ${gr.meses[iMin].slice(0, 4)}</text>`;
    if (iVuelve > 0 && iVuelve <= N) {
      const anios = Math.round(iVuelve / 12);
      document.getElementById("historia-texto").textContent =
        `La historia real, mes a mes. Quien puso 10.000 en acciones en enero de 2000 estuvo por debajo de lo que había puesto durante unos ${anios} años, hasta ${gr.meses[iVuelve].slice(0, 4)}. Después le ganó por lejos a todo lo demás.`;
    }
  }
  for (const i of [0, Math.round(N / 2), N])
    svg += `<text x="${X(i)}" y="216" font-size="10" fill="${GRIS}" text-anchor="${i === 0 ? "start" : i === N ? "end" : "middle"}">${gr.meses[i].slice(0, 4)}</text>`;
  document.getElementById("historia").innerHTML = svg;
  document.getElementById("leyenda").innerHTML = leyenda(gr.series.map(s => s.grupo));
  document.querySelectorAll(".sim").forEach(x => x.textContent = " " + datos.simbolo);
}

function pie() {
  const fiscal = datos.moneda === "EUR"
    ? `<p><b>Impuestos en España:</b> los ETF no se traspasan sin tributar como los fondos indexados: cada venta paga impuesto (19 a 30%). Por eso elegí ETFs de acumulación, que difieren el impuesto hasta que vendés. Si tenés más de 50.000 € en un broker extranjero, mirá el Modelo 720.</p>`
    : "";
  document.getElementById("pie").innerHTML = `
    <p>Datos a ${mes(datos.datos_al)} · se actualiza cada mes · datos desde ${datos.desde.slice(0, 4)}. Rendimientos en ${datos.moneda === "EUR" ? "euros" : "dólares"}, ya descontadas las comisiones. Antes de que existiera cada fondo se usa el índice que replica o un fondo parecido; en los bonos en euros anteriores a 2009, una aproximación con la tasa del gobierno alemán a 2 años (Bundesbank). La cuenta remunerada es una aproximación: tasa de referencia menos 0,5 puntos, nunca negativa.</p>
    ${fiscal}
    <h4 id="aviso">Aviso legal</h4>
    <p>Esta página es un proyecto personal con fines exclusivamente informativos y educativos. No constituye asesoramiento financiero, de inversión, fiscal ni legal, ni una recomendación personalizada, ni una oferta o solicitud de compra o venta de ningún instrumento financiero. "Recomendado" indica solo la elección del autor para un caso genérico, sin conocer tu situación, tus objetivos ni tu tolerancia al riesgo.</p>
    <p>El autor no es asesor financiero registrado ni está autorizado por la CNMV ni por ningún otro organismo. No tiene relación con los emisores ni con los brokers mencionados, y no recibe comisiones de nadie.</p>
    <p>Las rentabilidades pasadas no garantizan rentabilidades futuras. Toda inversión puede perder valor, incluido el capital invertido. Los datos salen de fuentes públicas (Yahoo Finance, Eurostat, FRED, BCE y fichas de los emisores), pueden tener errores o estar desactualizados, e incluyen aproximaciones: el índice o un fondo parecido antes del lanzamiento de cada fondo, bonos sintéticos y una cuenta remunerada modelada.</p>
    <p>Antes de invertir, leé el folleto y el documento de datos fundamentales (KID) de cada fondo y, si tenés dudas, consultá a un asesor financiero autorizado. El autor no se hace responsable de las decisiones que se tomen a partir de esta información.</p>`;
}

async function cargar(vista) {
  document.querySelectorAll("#moneda .chip").forEach(b => b.classList.toggle("on", b.dataset.m === vista));
  try {
    const r = await fetch(`data/${vista}.json`);
    if (!r.ok) throw new Error(r.status);
    datos = await r.json();
  } catch (e) {
    document.getElementById("grupos").innerHTML = `<div class="error">No pude cargar los datos (${esc(e.message)}). Probá recargar la página.</div>`;
    return;
  }
  grupos(); embudo(); grafico(); pie();
}

document.getElementById("moneda").addEventListener("click", e => {
  const b = e.target.closest("[data-m]"); if (!b) return;
  const u = new URL(location.href); u.searchParams.set("pais", b.dataset.m);
  history.replaceState(null, "", u);
  cargar(b.dataset.m);
});

document.getElementById("grupos").addEventListener("click", e => {
  const inst = e.target.closest(".inst[data-g]"); if (!inst) return;
  const chip = e.target.closest("[data-p]");
  const g = datos.grupos.find(x => x.id === inst.dataset.g), x = g.instrumentos[inst.dataset.j];
  if (chip) {
    inst.querySelectorAll("[data-p]").forEach(c => c.classList.toggle("on", c === chip));
    inst.querySelector(".escs").innerHTML = escenarios(x, chip.dataset.p, COLOR[g.id], escala(chip.dataset.p));
    return;
  }
  inst.classList.toggle("open");
});

cargar(vistaDeUrl());
