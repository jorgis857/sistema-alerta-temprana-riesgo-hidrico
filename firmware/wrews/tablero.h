// ============================================================================
//  WREWS - Paginas del tablero de control
//  Se sirven desde el ESP32 (servidor web embebido). Todo va en linea: sin
//  CDN ni librerias externas, porque la WLAN de la zona (o el hotspot de la
//  demo) puede no tener salida a internet. Las graficas se dibujan con
//  <canvas> a mano.
//
//  Datos: GET /api/actual (cada 2 s), /api/historial (cada 5 s),
//         /api/eventos?desde=N (cuando cambia ultimo_evento), /api/config.
//  Acciones: POST /api/silenciar, POST /logout,
//            GET y POST /api/parametros, POST /api/parametros/restaurar.
// ============================================================================
#pragma once

const char LOGIN_HTML[] PROGMEM = R"rawliteral(<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WREWS · Ingreso</title>
<style>
:root{--bg:#f4f6f8;--card:#fff;--txt:#1b2733;--sub:#5c6b7a;--acc:#0a6ebd;--err:#c62828;--borde:#d5dde5}
@media (prefers-color-scheme:dark){:root{--bg:#10161c;--card:#1a232c;--txt:#e6edf3;--sub:#9aa8b5;--acc:#4ea3e8;--err:#ef6b6b;--borde:#2c3946}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--txt);font:16px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px}
form{background:var(--card);border:1px solid var(--borde);border-radius:12px;padding:28px 24px;width:100%;max-width:340px}
h1{margin:0 0 4px;font-size:22px}p{margin:0 0 20px;color:var(--sub);font-size:14px}
label{display:block;font-size:13px;color:var(--sub);margin:12px 0 4px}
input{width:100%;padding:10px 12px;border:1px solid var(--borde);border-radius:8px;background:var(--bg);color:var(--txt);font-size:16px}
button{margin-top:20px;width:100%;padding:12px;border:0;border-radius:8px;background:var(--acc);color:#fff;font-size:16px;font-weight:600}
#msg{color:var(--err);font-size:14px;margin-top:12px;min-height:18px}
</style></head><body>
<form method="post" action="/login">
<h1>WREWS</h1><p>Tablero de control · acceso para autoridades</p>
<label for="u">Usuario</label><input id="u" name="u" autocomplete="username" required>
<label for="p">Clave</label><input id="p" name="p" type="password" autocomplete="current-password" required>
<button type="submit">Ingresar</button>
<div id="msg"></div>
</form>
<script>
const q=new URLSearchParams(location.search);
if(q.has('e'))document.getElementById('msg').textContent='Usuario o clave incorrectos.';
if(q.has('b'))document.getElementById('msg').textContent='Demasiados intentos. Espere 30 s.';
</script>
</body></html>)rawliteral";

const char TABLERO_HTML[] PROGMEM = R"rawliteral(<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WREWS · Tablero</title>
<style>
:root{--bg:#f4f6f8;--card:#fff;--txt:#1b2733;--sub:#5c6b7a;--borde:#d5dde5;--acc:#0a6ebd;
--ok:#2e7d32;--prec:#e0a100;--crit:#c62828;--fallo:#6a4c93;--grid:#e3e8ed;--linea:#0a6ebd}
@media (prefers-color-scheme:dark){:root{--bg:#10161c;--card:#1a232c;--txt:#e6edf3;--sub:#9aa8b5;--borde:#2c3946;--acc:#4ea3e8;
--ok:#4caf50;--prec:#f2c230;--crit:#ef5350;--fallo:#a786d6;--grid:#26313b;--linea:#4ea3e8}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:15px system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;border-bottom:1px solid var(--borde);background:var(--card);position:sticky;top:0;z-index:5}
header h1{margin:0;font-size:18px}header small{color:var(--sub);display:block;font-size:12px}
header button{background:none;border:1px solid var(--borde);color:var(--txt);border-radius:8px;padding:6px 10px;font-size:13px}
main{max-width:1100px;margin:0 auto;padding:16px;display:grid;gap:16px}
.card{background:var(--card);border:1px solid var(--borde);border-radius:12px;padding:14px 16px}
#aviso{display:none;border-radius:12px;padding:12px 16px;color:#fff;font-weight:600;align-items:center;justify-content:space-between;gap:12px}
#aviso button{background:rgba(255,255,255,.2);border:0;color:#fff;border-radius:6px;padding:4px 10px;font-size:13px}
#sinred{display:none;background:var(--fallo);color:#fff;border-radius:12px;padding:10px 16px;font-weight:600}
.estado{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;border-left:8px solid var(--ok)}
.estado .nom{font-size:28px;font-weight:700;letter-spacing:.5px}
.estado .det{color:var(--sub);font-size:13px;margin-top:2px}
#btnSil{padding:12px 16px;border:0;border-radius:8px;background:var(--crit);color:#fff;font-size:15px;font-weight:600}
#btnSil:disabled{background:var(--borde);color:var(--sub)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.m{border-top:4px solid var(--borde)}
.m .et{color:var(--sub);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
.m .v{font-size:24px;font-weight:700;margin-top:4px;font-variant-numeric:tabular-nums}
.m .u{font-size:13px;color:var(--sub);font-weight:400}
.m .n{font-size:12px;color:var(--sub);margin-top:2px;min-height:15px}
.s0{border-top-color:var(--ok)}.s1{border-top-color:var(--prec)}.s2{border-top-color:var(--crit)}
h2{font-size:15px;margin:0 0 10px}
.graf{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.graf .card{padding:12px}
.graf h3{margin:0 0 6px;font-size:13px;color:var(--sub);font-weight:600}
canvas{width:100%;height:150px;display:block}
#eventos{list-style:none;margin:0;padding:0;max-height:300px;overflow:auto}
#eventos li{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--borde);font-size:14px}
#eventos li:last-child{border-bottom:0}
#eventos .pt{width:10px;height:10px;border-radius:50%;margin-top:5px;flex:none}
#eventos .h{color:var(--sub);font-size:12px;white-space:nowrap;margin-left:auto}
footer{color:var(--sub);font-size:12px;text-align:center;padding:4px 16px 20px}
details.card>summary{cursor:pointer;font-weight:600;font-size:15px}
#conf .grupo{border-top:1px solid var(--borde);margin-top:14px;padding-top:12px}
#conf h3{margin:0 0 4px;font-size:14px}
#conf .ayuda{color:var(--sub);font-size:13px;margin:0 0 10px}
#conf .campos{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px 14px}
#conf label{display:block;font-size:12px;color:var(--sub);margin-bottom:3px}
#conf input,#conf select{width:100%;padding:8px 10px;border:1px solid var(--borde);border-radius:8px;background:var(--bg);color:var(--txt);font-size:15px}
#conf .vivo{font-size:13px;margin:8px 0 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
#conf .vivo b{font-variant-numeric:tabular-nums}
#conf button{padding:8px 12px;border:1px solid var(--borde);border-radius:8px;background:var(--card);color:var(--txt);font-size:13px}
#conf button.prim{background:var(--acc);border-color:var(--acc);color:#fff;font-size:15px;padding:10px 16px}
#conf .acciones{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:16px}
#confMsg{font-size:14px}
</style></head><body>
<header><div><h1>WREWS · Tablero de control</h1><small id="sub">Conectando…</small></div>
<form method="post" action="/logout"><button type="submit">Cerrar sesión</button></form></header>
<main>
<div id="sinred">Sin conexión con el equipo. Se reintenta cada 2 s; la alarma local sigue funcionando.</div>
<div id="aviso"><span id="avisoTxt"></span><button onclick="cerrarAviso()">Entendido</button></div>

<section class="card estado" id="est">
<div><div class="nom" id="estNom">—</div><div class="det" id="estDet"></div></div>
<button id="btnSil" disabled onclick="silenciar()">Silenciar alarma 15 min</button>
</section>

<section class="grid">
<div class="card m" id="cNivel"><div class="et">Nivel</div><div class="v"><span id="vNivel">—</span> <span class="u">%</span></div><div class="n" id="nNivel"></div></div>
<div class="card m" id="cTasa"><div class="et">Tasa de descenso</div><div class="v"><span id="vTasa">—</span> <span class="u">pp/min</span></div><div class="n" id="nTasa"></div></div>
<div class="card m" id="cEvap"><div class="et">Índice evaporativo</div><div class="v"><span id="vEvap">—</span> <span class="u">%</span></div><div class="n" id="nEvap"></div></div>
<div class="card m" id="cRiesgo"><div class="et">Riesgo hídrico</div><div class="v"><span id="vRiesgo">—</span> <span class="u">/100</span></div><div class="n" id="nRiesgo"></div></div>
<div class="card m"><div class="et">Evaporación (PT)</div><div class="v"><span id="vEt">—</span> <span class="u">mm/día</span></div><div class="n" id="nEt"></div></div>
<div class="card m"><div class="et">Irradiancia</div><div class="v"><span id="vRs">—</span> <span class="u">W/m²</span></div><div class="n" id="nRs"></div></div>
<div class="card m"><div class="et">Temperatura</div><div class="v"><span id="vT">—</span> <span class="u">°C</span></div></div>
<div class="card m"><div class="et">Humedad relativa</div><div class="v"><span id="vHr">—</span> <span class="u">%</span></div></div>
<div class="card m"><div class="et">Presión</div><div class="v"><span id="vP">—</span> <span class="u">hPa</span></div></div>
<div class="card m"><div class="et">Déficit de vapor</div><div class="v"><span id="vVpd">—</span> <span class="u">kPa</span></div><div class="n" id="nVpd"></div></div>
</section>

<section>
<h2>Histórico reciente <span id="hDur" style="color:var(--sub);font-weight:400"></span></h2>
<div class="graf">
<div class="card"><h3>Nivel (%)</h3><canvas id="gNivel"></canvas></div>
<div class="card"><h3>Riesgo hídrico (0–100)</h3><canvas id="gRiesgo"></canvas></div>
<div class="card"><h3>Índice evaporativo (%)</h3><canvas id="gEvap"></canvas></div>
<div class="card"><h3>Tasa de descenso (pp/min)</h3><canvas id="gTasa"></canvas></div>
<div class="card"><h3>Temperatura (°C)</h3><canvas id="gTemp"></canvas></div>
<div class="card"><h3>Irradiancia (W/m²)</h3><canvas id="gIrr"></canvas></div>
</div>
</section>

<section class="card"><h2>Eventos</h2><ul id="eventos"><li><span class="h">Sin eventos todavía</span></li></ul></section>

<details class="card" id="conf" ontoggle="if(this.open)cargarConf()">
<summary>Configuración y calibración</summary>
<p class="ayuda" style="margin-top:10px">Los cambios se aplican de inmediato y se guardan en el equipo: se conservan aunque se apague. Los pesos y los umbrales de nivel, riesgo y evaporación son fijos porque están justificados con referencias.</p>

<div class="grupo"><h3>Nivel: distancias del sensor al agua</h3>
<p class="ayuda">Llene el tubo, espere a que la lectura se estabilice y pulse «Usar como lleno»; repita con el tubo vacío. Por la zona ciega del sensor, «lleno» debe quedar a 5 cm o más.</p>
<div class="campos">
<div><label for="p_d_lleno">Tubo lleno (cm)</label><input id="p_d_lleno" type="number" step="0.1"></div>
<div><label for="p_d_vacio">Tubo vacío (cm)</label><input id="p_d_vacio" type="number" step="0.1"></div>
</div>
<div class="vivo">Distancia medida ahora: <b id="lDist">—</b> cm
<button type="button" onclick="usarDist('p_d_lleno')">Usar como lleno</button>
<button type="button" onclick="usarDist('p_d_vacio')">Usar como vacío</button></div>
</div>

<div class="grupo"><h3>Piranómetro: constante del panel</h3>
<p class="ayuda">Calibre con sol, no con la lámpara. Escriba la irradiancia de la referencia (piranómetro o estación) en el mismo momento y pulse «Calcular K».</p>
<div class="campos">
<div><label for="p_k_panel">K del panel ((W/m²)/mA)</label><input id="p_k_panel" type="number" step="0.01"></div>
<div><label for="refIrr">Irradiancia de referencia (W/m²)</label><input id="refIrr" type="number" step="1"></div>
</div>
<div class="vivo">Corriente del panel ahora: <b id="lCorr">—</b> mA
<button type="button" onclick="calcK()">Calcular K</button></div>
</div>

<div class="grupo"><h3>Tasa de descenso</h3>
<p class="ayuda">Si cambia el recorrido del tubo, repita las dos maniobras de descenso para recalibrar estos valores.</p>
<div class="campos">
<div><label for="p_u_prec_tasa">Precaución (pp/min)</label><input id="p_u_prec_tasa" type="number" step="0.1"></div>
<div><label for="p_u_crit_tasa">Crítico (pp/min)</label><input id="p_u_crit_tasa" type="number" step="0.1"></div>
<div><label for="p_salto">Salto de discontinuidad (pp)</label><input id="p_salto" type="number" step="0.1"></div>
</div></div>

<div class="grupo"><h3>Evaporación</h3>
<p class="ayuda">En modo demo, el promedio de luz de la ventana corta se toma como el mediodía de un día con esa nubosidad. En campo se usan las 24 h reales. Cambiar el modo o la ventana reinicia la estimación.</p>
<div class="campos">
<div><label for="p_modo_demo">Modo</label><select id="p_modo_demo"><option value="1">Demo (ventana corta = mediodía)</option><option value="0">Campo (24 h)</option></select></div>
<div><label for="p_vent_demo">Ventana demo (s)</label><input id="p_vent_demo" type="number" step="1"></div>
<div><label for="p_et_ref">ET de referencia (mm/día)</label><input id="p_et_ref" type="number" step="0.01"></div>
</div></div>

<div class="acciones">
<button type="button" class="prim" onclick="guardarConf()">Guardar cambios</button>
<button type="button" onclick="restaurarConf()">Restaurar valores de fábrica</button>
<span id="confMsg"></span></div>
</details>
</main>
<footer id="pie"></footer>

<script>
const $=id=>document.getElementById(id);
const NOM={NORMAL:'Normal',PRECAUCION:'Precaución',CRITICO:'Crítico',FALLO:'Fallo del equipo'};
const COLOR=['--ok','--prec','--crit','--fallo'];
let cfg={}, hist=[], eventos=[], ultimoEv=-1, ultimo=null, audio=null;

const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const fmt=(v,d)=>v==null?'—':Number(v).toFixed(d);
function dur(s){s=Math.max(0,Math.round(s));if(s<60)return s+' s';const m=Math.floor(s/60);return m<60?m+' min '+(s%60)+' s':Math.floor(m/60)+' h '+(m%60)+' min';}

// Toda peticion se corta a los ms_max: si la WLAN se cae, el navegador
// dejaria la peticion colgada uno o dos minutos y, con varias acumuladas,
// las nuevas quedarian en fila aunque el equipo ya hubiera vuelto.
async function api(u,o,ms_max){
  const ctl=new AbortController(),tm=setTimeout(()=>ctl.abort(),ms_max||4000);
  try{
    const r=await fetch(u,Object.assign({cache:'no-store',credentials:'same-origin',signal:ctl.signal},o||{}));
    if(r.status==401||r.status==403){location.href='/login';throw new Error('sesion');}
    if(!r.ok)throw new Error('http '+r.status);
    return await r.json();
  }finally{clearTimeout(tm);}
}

// El navegador solo deja sonar audio despues de un toque del usuario
document.addEventListener('click',()=>{if(!audio){try{audio=new(window.AudioContext||window.webkitAudioContext)();}catch(e){}}},{once:true});
function pitido(grav){
  if(!audio)return;
  const o=audio.createOscillator(),g=audio.createGain();
  o.frequency.value=grav>=2?2500:1000;o.connect(g);g.connect(audio.destination);
  g.gain.setValueAtTime(.2,audio.currentTime);o.start();o.stop(audio.currentTime+(grav>=2?.6:.25));
}

function avisar(ev){
  const a=$('aviso');
  a.style.display='flex';a.style.background=css(COLOR[Math.min(ev.gravedad,2)]);
  if(ev.gravedad==0)a.style.background=css('--acc');
  $('avisoTxt').textContent=ev.texto;
  if(ev.gravedad>=1){pitido(ev.gravedad);if(navigator.vibrate)navigator.vibrate([200,100,200]);}
}
function cerrarAviso(){$('aviso').style.display='none';}

function tarjeta(id,sev){const c=$(id);c.classList.remove('s0','s1','s2');c.classList.add('s'+Math.min(sev,2));}

function pintar(a){
  ultimo=a;
  const est=$('est');est.style.borderLeftColor=css(COLOR[a.estado_n]);
  $('estNom').textContent=NOM[a.estado]||a.estado;$('estNom').style.color=css(COLOR[a.estado_n]);
  let det=a.silenciado?'Buzzer silenciado, quedan '+dur(a.silencio_rest_s)+'. ':'';
  if(a.estado_n==3)det+='Revise el sensor de nivel o el BME280.';
  else det+='Severidad · nivel '+a.sev_nivel+' · evaporación '+a.sev_evap+' · tasa '+a.sev_tasa+' · riesgo '+a.sev_riesgo;
  $('estDet').textContent=det;
  const b=$('btnSil');b.disabled=a.estado_n==0||a.silenciado;
  b.textContent=a.silenciado?'Silenciada':'Silenciar alarma 15 min';

  $('vNivel').textContent=a.ultra_ok?fmt(a.nivel_pct,1):'Sin eco';
  $('nNivel').textContent=a.ultra_ok?'Distancia '+fmt(a.distancia_cm,1)+' cm':'El sensor no responde';
  tarjeta('cNivel',a.sev_nivel);
  $('vTasa').textContent=a.tasa_lista?fmt(a.tasa_ppm,1):'…';
  $('nTasa').textContent=a.tasa_lista?'Máx. '+fmt(a.tasa_max,1)+' pp/min':'Midiendo tendencia';
  tarjeta('cTasa',a.sev_tasa);
  // La evaporacion sola llega como maximo a precaucion: se aclara cuando su severidad es 2
  if(a.estado_evap=='OK'){$('vEvap').textContent=fmt(a.idx_evap,1);
    $('nEvap').textContent=a.sev_evap>=2?'Demanda extrema · sola cuenta como precaución':'Priestley-Taylor + VPD';}
  else{$('vEvap').textContent='…';$('nEvap').textContent='Estimación en curso ('+Math.round(a.cobertura_ventana*100)+' % de la ventana)';}
  tarjeta('cEvap',a.sev_evap);
  $('vRiesgo').textContent=fmt(a.riesgo,1);
  $('nRiesgo').textContent='Pesos '+Math.round(cfg.w_nivel*100)+'/'+Math.round(cfg.w_evap*100)+'/'+Math.round(cfg.w_tasa*100);
  tarjeta('cRiesgo',a.sev_riesgo);
  $('vEt').textContent=a.estado_evap=='OK'?fmt(a.et_mm_dia,2):'…';
  $('nEt').textContent='Rn '+fmt(a.rn_mj,1)+' MJ/m²·día · modo '+a.modo;
  $('vRs').textContent=fmt(a.rs_wm2,0);
  $('nRs').textContent='Día equiv. '+fmt(a.rs_dia_mj,1)+' MJ/m²';
  $('vT').textContent=fmt(a.temp_c,1);$('vHr').textContent=fmt(a.hum_pct,1);
  $('vP').textContent=fmt(a.pres_hpa,1);$('vVpd').textContent=fmt(a.vpd_kpa,2);
  $('nVpd').textContent=a.estado_evap=='OK'?'Promedio de la ventana '+fmt(a.vpd_ventana_kpa,2)+' kPa':'';

  const edad=(a.t_ms-a.t_muestra_ms)/1000;
  $('sub').textContent='Red '+(a.red||cfg.red||'')+' · señal '+a.rssi+' dBm · dato de hace '+edad.toFixed(1)+' s';
  $('pie').textContent='Equipo encendido hace '+dur(a.t_ms/1000)+' · reconexiones Wi-Fi: '+a.reconexiones_wifi+' · modo '+a.modo;
  document.title=(a.estado_n>0?'⚠ ':'')+'WREWS · '+(NOM[a.estado]||a.estado);
  if($('conf').open)vivoConf(a.ultra_ok?a.distancia_cm:null,a.corriente_ma);
  pintarEventos();
}

function pintarEventos(){
  if(!eventos.length||!ultimo)return;
  $('eventos').innerHTML='';
  for(const e of eventos.slice().reverse()){
    const li=document.createElement('li');
    const pt=document.createElement('span');pt.className='pt';
    pt.style.background=css(e.gravedad==0?'--acc':COLOR[e.gravedad]);
    const tx=document.createElement('span');tx.textContent=e.texto;
    const h=document.createElement('span');h.className='h';h.textContent='hace '+dur((ultimo.t_ms-e.t_ms)/1000);
    li.append(pt,tx,h);$('eventos').append(li);
  }
}

async function traerEventos(){
  const r=await api('/api/eventos?desde='+Math.max(ultimoEv,0));
  const nuevos=r.eventos;
  if(ultimoEv>=0)for(const e of nuevos)avisar(e);   // en la primera carga no se avisa lo viejo
  eventos=eventos.concat(nuevos).slice(-50);
  if(nuevos.length)ultimoEv=nuevos[nuevos.length-1].id;
  else if(ultimoEv<0)ultimoEv=0;
}

let enLinea=true;
async function ciclo(){
  try{
    const a=await api('/api/actual');
    $('sinred').style.display='none';
    if(a.ultimo_evento!=ultimoEv)await traerEventos();
    pintar(a);
    if(!enLinea){enLinea=true;traerHistorial();}   // al volver, ponerse al dia ya
  }catch(e){if(e.message!='sesion'){enLinea=false;$('sinred').style.display='block';}}
}

// ---- Graficas -------------------------------------------------------------
// Columnas de /api/historial: t_s, nivel, riesgo, evap, tasa, temp, hum, irr, estado
function grafica(id,col,lo,hi,umbrales){
  const c=$(id),r=window.devicePixelRatio||1,W=c.clientWidth,H=c.clientHeight;
  c.width=W*r;c.height=H*r;const g=c.getContext('2d');g.scale(r,r);g.clearRect(0,0,W,H);
  const P={l:36,r:8,t:8,b:18};
  g.font='11px system-ui,sans-serif';g.fillStyle=css('--sub');
  if(hist.length<2){g.fillText('Juntando datos…',P.l,H/2);return;}
  const t1=hist[hist.length-1][0],t0=hist[0][0];
  const vals=hist.map(p=>p[col]).filter(v=>v!=null);
  if(lo==null)lo=Math.min(...vals);if(hi==null)hi=Math.max(...vals);
  if(hi-lo<1){hi+=.5;lo-=.5;}
  const X=t=>P.l+(t-t0)/Math.max(t1-t0,1)*(W-P.l-P.r);
  const Y=v=>H-P.b-(v-lo)/(hi-lo)*(H-P.t-P.b);
  g.strokeStyle=css('--grid');g.lineWidth=1;
  for(const v of [lo,(lo+hi)/2,hi]){g.beginPath();g.moveTo(P.l,Y(v));g.lineTo(W-P.r,Y(v));g.stroke();
    g.fillText(Math.abs(hi-lo)>=10?v.toFixed(0):v.toFixed(1),2,Y(v)+4);}
  g.fillText('hace '+dur(t1-t0),P.l,H-4);g.textAlign='right';g.fillText('ahora',W-P.r,H-4);g.textAlign='left';
  for(const [u,cv] of (umbrales||[])){
    if(u<lo||u>hi)continue;
    g.strokeStyle=css(cv);g.setLineDash([4,4]);g.beginPath();g.moveTo(P.l,Y(u));g.lineTo(W-P.r,Y(u));g.stroke();g.setLineDash([]);
  }
  g.strokeStyle=css('--linea');g.lineWidth=2;g.beginPath();let dentro=false;
  for(const p of hist){const v=p[col];if(v==null){dentro=false;continue;}
    if(!dentro){g.moveTo(X(p[0]),Y(v));dentro=true;}else g.lineTo(X(p[0]),Y(v));}
  g.stroke();
}
function pintarGraficas(){
  grafica('gNivel',1,0,100,[[cfg.u_prec_nivel,'--prec'],[cfg.u_crit_nivel,'--crit']]);
  grafica('gRiesgo',2,0,100,[[cfg.u_prec_riesgo,'--prec'],[cfg.u_crit_riesgo,'--crit']]);
  grafica('gEvap',3,0,100,[[cfg.u_prec_evap,'--prec'],[cfg.u_crit_evap,'--crit']]);
  grafica('gTasa',4,0,null,[[cfg.u_prec_tasa,'--prec'],[cfg.u_crit_tasa,'--crit']]);
  grafica('gTemp',5,null,null,[]);
  grafica('gIrr',7,0,null,[]);
  if(hist.length>1)$('hDur').textContent='· últimos '+dur(hist[hist.length-1][0]-hist[0][0])+', un punto cada '+cfg.hist_cada_s+' s';
}
async function traerHistorial(){try{hist=await api('/api/historial',null,8000);pintarGraficas();}catch(e){}}

// Cada ciclo arranca cuando el anterior termino (no setInterval): nunca hay
// dos peticiones del mismo tipo en vuelo.
function repetir(fn,ms){const paso=async()=>{await fn();setTimeout(paso,ms);};setTimeout(paso,ms);}

// ---- Configuracion y calibracion -----------------------------------------
// Mismos nombres que /api/parametros (GET y POST)
const CAMPOS=['d_lleno','d_vacio','k_panel','u_prec_tasa','u_crit_tasa','salto','et_ref','modo_demo','vent_demo'];
function msgConf(t,tipo){const m=$('confMsg');m.textContent=t;m.style.color=css(tipo=='err'?'--crit':tipo=='ok'?'--ok':'--sub');}
function vivoConf(d,i){$('lDist').textContent=fmt(d,1);$('lCorr').textContent=fmt(i,2);}
function llenarConf(p){
  for(const k of CAMPOS){const e=$('p_'+k);e.value=p[k];e.title='De fábrica: '+p['def_'+k];}
  vivoConf(p.distancia_cm,p.corriente_ma);
}
async function cargarConf(){
  try{llenarConf(await api('/api/parametros'));msgConf('');}
  catch(e){msgConf('No se pudo leer la configuración','err');}
}
function usarDist(id){
  if(!ultimo||!ultimo.ultra_ok||ultimo.distancia_cm==null){msgConf('El sensor de nivel no da lectura ahora','err');return;}
  $(id).value=ultimo.distancia_cm.toFixed(1);msgConf('Falta pulsar «Guardar cambios»');
}
function calcK(){
  const ref=parseFloat($('refIrr').value),i=ultimo?ultimo.corriente_ma:null;
  if(!(ref>0)){msgConf('Escriba la irradiancia de referencia','err');return;}
  if(!(i>0.05)){msgConf('La corriente del panel es casi cero: calibre con sol','err');return;}
  $('p_k_panel').value=(ref/i).toFixed(2);msgConf('Falta pulsar «Guardar cambios»');
}
async function enviarConf(url,cuerpo){
  msgConf('Guardando…');
  const ctl=new AbortController(),tm=setTimeout(()=>ctl.abort(),8000);
  try{
    const r=await fetch(url,{method:'POST',body:cuerpo,credentials:'same-origin',signal:ctl.signal});
    if(r.status==401||r.status==403){location.href='/login';return;}
    const j=await r.json().catch(()=>({}));
    if(!r.ok){msgConf(j.error||('Error '+r.status),'err');return;}
    llenarConf(j);msgConf('Guardado y aplicado en el equipo','ok');
    try{cfg=await api('/api/config');}catch(e){}
    traerHistorial();ciclo();
  }catch(e){msgConf('Sin conexión con el equipo: no se guardó','err');}
  finally{clearTimeout(tm);}
}
function guardarConf(){
  const b=new URLSearchParams();for(const k of CAMPOS)b.append(k,$('p_'+k).value);
  enviarConf('/api/parametros',b);
}
function restaurarConf(){
  if(confirm('¿Volver a los valores de fábrica? Se pierde la calibración guardada.'))
    enviarConf('/api/parametros/restaurar',new URLSearchParams());
}

async function silenciar(){
  $('btnSil').disabled=true;
  try{await api('/api/silenciar',{method:'POST'});}catch(e){}
  ciclo();
}

(async()=>{
  try{cfg=await api('/api/config');}catch(e){}
  await ciclo();await traerHistorial();
  repetir(ciclo,2000);repetir(traerHistorial,5000);
  addEventListener('resize',pintarGraficas);
})();
</script>
</body></html>)rawliteral";
