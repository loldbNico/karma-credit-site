import re

# Read the file
with open('NEON CITY MAP.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the script start and end
script_start = content.find('<script>')
script_end = content.find('</script>', script_start) + len('</script>')

if script_start != -1 and script_end != -1:
    print(f'Found script from {script_start} to {script_end}')
    
    # The corrected script content
    new_script = '''  <script>
/**
 * CONFIG
 */
const SVG_URL = "./map.svg";

/* =========================
   BOOT CONTROLLER
   ========================= */
const boot = {
  el: document.getElementById("boot"),
  linesEl: document.getElementById("bootLines"),
  fillEl: document.getElementById("bootFill"),
  pctEl: document.getElementById("bootPct"),
  phaseEl: document.getElementById("bootPhase"),
  hintEl: document.getElementById("bootHint"),
};

function bootLine(text, dim=false){
  if(!boot.linesEl) return;
  const div = document.createElement("div");
  div.className = "boot-line" + (dim ? " dim" : "");
  div.textContent = text;
  boot.linesEl.appendChild(div);
  boot.linesEl.scrollTop = boot.linesEl.scrollHeight;
}

function bootSet(pct, phase){
  pct = Math.max(0, Math.min(100, pct));
  boot.fillEl && (boot.fillEl.style.width = pct + "%");
  boot.pctEl && (boot.pctEl.textContent = Math.round(pct) + "%");
  boot.phaseEl && (boot.phaseEl.textContent = phase || "");
}

function bootClose(){
  if(!boot.el) return;
  boot.el.classList.add("off");
  setTimeout(() => boot.el.classList.add("hidden"), 420);
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

/* =========================
   TERMINAL LOG
   ========================= */
function term(msg){
  const log = document.getElementById("termLog");
  if(!log) return;
  const div = document.createElement("div");
  div.className = "termline";
  div.textContent = msg;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

/* =========================
   SVG + CAMERA STATE
   ========================= */
let svgEl = null;
let selectedEl = null;

const host = document.getElementById("svgHost");
const tooltip = document.getElementById("tooltip");
const zoomReadout = document.getElementById("zoomReadout");
const panReadout = document.getElementById("panReadout");
const loadStateEl = document.getElementById("loadState");

const mapwrap = document.querySelector(".mapwrap");

const camera = {
  x: 0, y: 0,
  zoom: 1,
  targetX: 0, targetY: 0,
  targetZoom: 1,
  minZoom: 0.4,
  maxZoom: 9,
  panSmooth: 0.18,
  zoomSmooth: 0.20,
  vb: null,
  vw: 1, vh: 1,
  anim: null
};

function updateViewport(){
  const r = mapwrap.getBoundingClientRect();
  camera.vw = r.width;
  camera.vh = r.height;
}
updateViewport();
new ResizeObserver(updateViewport).observe(mapwrap);

let perfTimer = null;
function perfOn(){
  document.body.classList.add("perf");
  if(perfTimer) clearTimeout(perfTimer);
  perfTimer = setTimeout(() => document.body.classList.remove("perf"), 140);
}

function clamp(n,a,b){ return Math.max(a, Math.min(b,n)); }
function lerp(a,b,t){ return a + (b-a)*t; }
function easeOutCubic(t){ return 1 - Math.pow(1-t,3); }

function clampToBounds(){
  if(!camera.vb) return;

  const vb = camera.vb;
  const halfW = (camera.vw / 2) / camera.targetZoom;
  const halfH = (camera.vh / 2) / camera.targetZoom;
  const pad = 40 / camera.targetZoom;

  const minX = vb.x + halfW - pad;
  const maxX = vb.x + vb.width - halfW + pad;
  const minY = vb.y + halfH - pad;
  const maxY = vb.y + vb.height - halfH + pad;

  camera.targetX = clamp(camera.targetX, minX, maxX);
  camera.targetY = clamp(camera.targetY, minY, maxY);
}

function renderCamera(){
  const cx = camera.vw / 2;
  const cy = camera.vh / 2;
  host.style.transform =
    `translate3d(${cx}px, ${cy}px, 0) scale(${camera.zoom}) translate(${-camera.x}px, ${-camera.y}px)`;

  if(zoomReadout) zoomReadout.textContent = `ZOOM: ${Math.round(camera.zoom * 100)}%`;
  if(panReadout) panReadout.textContent = `${Math.round(camera.x)},${Math.round(camera.y)}`;
}

function cameraSetInstant(x,y,z){
  camera.x = camera.targetX = x;
  camera.y = camera.targetY = y;
  camera.zoom = camera.targetZoom = z;
  clampToBounds();
  renderCamera();
}

function cameraFlyTo(x,y,z, dur=520){
  camera.anim = {
    t0: performance.now(),
    dur,
    from: { x: camera.targetX, y: camera.targetY, zoom: camera.targetZoom },
    to: { x, y, zoom: z }
  };
  perfOn();
}

let rafStarted = false;
function startRAF(){
  if(rafStarted) return;
  rafStarted = true;

  const tick = () => {
    requestAnimationFrame(tick);

    if(camera.anim){
      const t = (performance.now() - camera.anim.t0) / camera.anim.dur;
      const k = easeOutCubic(clamp(t,0,1));
      camera.targetX = lerp(camera.anim.from.x, camera.anim.to.x, k);
      camera.targetY = lerp(camera.anim.from.y, camera.anim.to.y, k);
      camera.targetZoom = lerp(camera.anim.from.zoom, camera.anim.to.zoom, k);
      clampToBounds();
      if(t >= 1) camera.anim = null;
    }

    camera.zoom = lerp(camera.zoom, camera.targetZoom, camera.zoomSmooth);
    camera.x = lerp(camera.x, camera.targetX, camera.panSmooth);
    camera.y = lerp(camera.y, camera.targetY, camera.panSmooth);
    renderCamera();
  };

  tick();
}

/* =========================
   INPUT (PAN/ZOOM)
   ========================= */
let isDragging = false;
let last = {x:0,y:0};

host.addEventListener("mousedown", (e) => {
  isDragging = true;
  last.x = e.clientX;
  last.y = e.clientY;
  host.classList.add("grabbing");
  perfOn();
});

window.addEventListener("mouseup", () => {
  isDragging = false;
  host.classList.remove("grabbing");
});

window.addEventListener("mousemove", (e) => {
  if(!isDragging) return;
  const dx = e.clientX - last.x;
  const dy = e.clientY - last.y;

  camera.targetX -= dx / camera.targetZoom;
  camera.targetY -= dy / camera.targetZoom;

  last.x = e.clientX;
  last.y = e.clientY;

  clampToBounds();
  perfOn();
});

mapwrap.addEventListener("wheel", (e) => {
  e.preventDefault();
  const rect = mapwrap.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  const wx = camera.targetX + (mx - camera.vw/2) / camera.targetZoom;
  const wy = camera.targetY + (my - camera.vh/2) / camera.targetZoom;

  const factor = e.deltaY < 0 ? 1.12 : 0.89;
  const newZ = clamp(camera.targetZoom * factor, camera.minZoom, camera.maxZoom);
  if(newZ === camera.targetZoom) return;

  camera.targetZoom = newZ;
  camera.targetX = wx - (mx - camera.vw/2) / camera.targetZoom;
  camera.targetY = wy - (my - camera.vh/2) / camera.targetZoom;

  clampToBounds();
  perfOn();
}, { passive:false });

/* =========================
   TOOLTIP + LABELS
   ========================= */
function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, (m) => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[m]));
}

function regionLabel(el){
  const name = el.getAttribute("data-name") || el.id || "(unnamed)";
  const id = el.id ? `#${el.id}` : "(no id)";
  const zone = (el.getAttribute("data-zone") || "").toLowerCase();
  return { name, id, zone };
}

function onEnter(e){
  const { name, id, zone } = regionLabel(e.currentTarget);
  tooltip.innerHTML = `${escapeHtml(name)} <span style="color:var(--muted)">${escapeHtml(id)}${zone ? " • " + escapeHtml(zone) : ""}</span>`;
  tooltip.classList.add("on");
}
function onMove(e){
  tooltip.style.left = `${e.clientX}px`;
  tooltip.style.top = `${e.clientY}px`;
}
function onLeave(){
  tooltip.classList.remove("on");
}

/* =========================
   DETAILS PANEL (RIGHT)
   ========================= */
function setDetails(el){
  const { name, id, zone } = regionLabel(el);
  const type =
    el.classList.contains("building") ? "building" :
    el.classList.contains("road") ? "road" :
    el.classList.contains("wall") ? "wall" :
    el.classList.contains("region") ? "region" : "unknown";

  let boundsTxt = "—";
  try{
    const b = el.getBBox();
    boundsTxt = `${Math.round(b.width)}×${Math.round(b.height)}`;
    if(type !== "road" && type !== "wall"){
      document.getElementById("dBounds").textContent = boundsTxt;
    } else {
      document.getElementById("dBounds").textContent = "path";
    }
  }catch{
    document.getElementById("dBounds").textContent = "—";
  }

  document.getElementById("detailState").textContent = "TARGET";
  document.getElementById("dName").textContent = name;
  document.getElementById("dId").textContent = id;
  document.getElementById("dType").textContent = type;
  document.getElementById("dZone").textContent = zone || "—";
  document.getElementById("detailFoot").textContent = "active";
}

function clearDetails(){
  document.getElementById("detailState").textContent = "NO TARGET";
  document.getElementById("dName").textContent = "—";
  document.getElementById("dId").textContent = "—";
  document.getElementById("dType").textContent = "—";
  document.getElementById("dZone").textContent = "—";
  document.getElementById("dBounds").textContent = "—";
  document.getElementById("detailFoot").textContent = "waiting";
}

/* =========================
   REGION COLORING
   ========================= */
function hashToHue(str){
  let h = 2166136261;
  for(let i=0;i<str.length;i++){
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h) % 360;
}

function colorizeRegions(){
  if(!svgEl) return;
  svgEl.querySelectorAll(".region").forEach((r, i) => {
    if(r.classList.contains("wall")) return;
    const key = r.id || r.getAttribute("data-name") || String(i);
    const hue = hashToHue(key);
    r.style.fill = `hsla(${hue}, 75%, 55%, 0.16)`;
  });
}

/* =========================
   FLY TO ELEMENT
   ========================= */
function flyToElement(el, zoomMin=2.2){
  try{
    const b = el.getBBox();
    const cx = b.x + b.width/2;
    const cy = b.y + b.height/2;

    const fitX = camera.vw / (b.width + 120);
    const fitY = camera.vh / (b.height + 120);
    const fit = clamp(Math.min(fitX, fitY), camera.minZoom, camera.maxZoom);

    const z = clamp(Math.max(zoomMin, fit), camera.minZoom, camera.maxZoom);
    cameraFlyTo(cx, cy, z, 520);
  }catch{}
}

/* =========================
   FILTER BUTTONS (HUD)
   ========================= */
document.querySelectorAll(".hudf").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".hudf").forEach(x => x.classList.remove("on"));
    btn.classList.add("on");

    if(!svgEl) return;
    const preset = btn.getAttribute("data-preset");
    const regions = Array.from(svgEl.querySelectorAll(".region:not(.wall)"));

    if(preset === "all"){
      regions.forEach(r => r.classList.remove("dimmed"));
      return;
    }

    regions.forEach(r => {
      const zone = (r.getAttribute("data-zone") || "").toLowerCase();
      r.classList.toggle("dimmed", zone !== preset);
    });
  });
});

/* =========================
   LIVE FEED TABS (LEFT)
   ========================= */
document.querySelectorAll(".liveTab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".liveTab").forEach(b => b.classList.remove("on"));
    btn.classList.add("on");
    const tab = btn.getAttribute("data-tab");
    document.getElementById("paneWeather").classList.toggle("on", tab === "weather");
    document.getElementById("paneNews").classList.toggle("on", tab === "news");
  });
});

/* =========================
   WEATHER + NEWS (NO CRASH)
   ========================= */
async function fetchWeather(){
  try{
    const res = await fetch("https://api.open-meteo.com/v1/forecast?latitude=52.2298&longitude=21.0118&current=temperature_2m,wind_speed_10m,weather_code&timezone=Europe%2FWarsaw");
    const data = await res.json();
    const c = data.current || {};
    document.getElementById("wxTemp").textContent = (c.temperature_2m ?? "—") + "°C";
    document.getElementById("wxWind").textContent = (c.wind_speed_10m ?? "—") + " km/h";
    document.getElementById("wxCode").textContent = String(c.weather_code ?? "—");
    document.getElementById("wxUpdated").textContent = "updated: " + new Date().toLocaleTimeString();
  }catch{
    document.getElementById("wxUpdated").textContent = "weather link failed";
  }
}

async function fetchNews(){
  try{
    const res = await fetch("https://api.gdeltproject.org/api/v2/doc/doc?query=warsaw%20OR%20poland&mode=artlist&maxrecords=5&format=json");
    const data = await res.json();
    const list = document.getElementById("newsList");
    list.innerHTML = "";
    const arts = data.articles || [];
    if(!arts.length){
      list.innerHTML = `<div class="newsItem dim">no headlines</div>`;
    } else {
      arts.slice(0,5).forEach(a => {
        const div = document.createElement("div");
        div.className = "newsItem";
        div.innerHTML = `<div class="nTitle">${escapeHtml(a.title || "—")}</div><div class="nDesc">${escapeHtml(a.seendate || "")}</div>`;
        list.appendChild(div);
      });
    }
    document.getElementById("newsUpdated").textContent = "updated: " + new Date().toLocaleTimeString();
  }catch{
    document.getElementById("newsUpdated").textContent = "news link failed";
  }
}

/* =========================
   SVG LOADER (CANNOT STALL)
   ========================= */
async function loadSvg(){
  try{
    loadStateEl && (loadStateEl.textContent = "downloading");
    term("[SVG] fetch initiated");
    bootLine("[SVG] downloading payload…");

    const res = await fetch(SVG_URL, { cache: "no-store" });
    if(!res.ok) throw new Error(`Failed to load SVG (${res.status})`);

    // simple load (fast + reliable). stream progress is optional later.
    const txt = await res.text();
    host.innerHTML = txt;

    svgEl = host.querySelector("svg");
    if(!svgEl) throw new Error("No <svg> element found in file.");

    svgEl.style.width = "100%";
    svgEl.style.height = "100%";
    svgEl.style.maxWidth = "none";
    svgEl.style.maxHeight = "none";

    if(!svgEl.getAttribute("viewBox")){
      const w = parseFloat(svgEl.getAttribute("width")) || 1920;
      const h = parseFloat(svgEl.getAttribute("height")) || 1080;
      svgEl.setAttribute("viewBox", `0 0 ${w} ${h}`);
    }

    // bounds + center
    const vb = svgEl.viewBox.baseVal;
    camera.vb = { x: vb.x, y: vb.y, width: vb.width, height: vb.height };

    // wire up everything (regions/roads/buildings/walls)
    bootSet(88, "wiring");
    loadStateEl && (loadStateEl.textContent = "wiring");
    term("[SVG] wiring elements…");

    const clickable = svgEl.querySelectorAll(".region, .road, .building, .wall, [data-region='true']");
    clickable.forEach(el => {
      // If they used data-region=true but no class, treat as region
      if(el.getAttribute("data-region") === "true" && !el.classList.contains("region")){
        el.classList.add("region");
      }

      el.style.cursor = "pointer";
      el.addEventListener("mouseenter", onEnter);
      el.addEventListener("mousemove", onMove);
      el.addEventListener("mouseleave", onLeave);

      el.addEventListener("click", (e) => {
        e.stopPropagation();
        if(selectedEl) selectedEl.classList.remove("selected");
        selectedEl = el;
        selectedEl.classList.add("selected");
        setDetails(el);

        // fly only for regions/buildings (roads/walls are paths)
        if(el.classList.contains("region") && !el.classList.contains("wall")) flyToElement(el, 2.2);
        if(el.classList.contains("building")) flyToElement(el, 2.6);
      });

      el.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        if(el.classList.contains("region") && !el.classList.contains("wall")) flyToElement(el, 3.0);
        if(el.classList.contains("building")) flyToElement(el, 3.2);
      });
    });

    svgEl.addEventListener("click", () => {
      if(selectedEl) selectedEl.classList.remove("selected");
      selectedEl = null;
      clearDetails();
      term("[CLEAR] selection cleared");
    });

    colorizeRegions();

    cameraSetInstant(vb.x + vb.width/2, vb.y + vb.height/2, 1);
    startRAF();

    bootSet(100, "ready");
    boot.hintEl && (boot.hintEl.textContent = "MAP UNLOCKED");
    bootLine("[OK] map online");
    loadStateEl && (loadStateEl.textContent = "ready");
    term("[SVG] ready");

    setTimeout(bootClose, 260);

  }catch(err){
    bootSet(100, "error");
    boot.hintEl && (boot.hintEl.textContent = "LINK FAILED");
    bootLine("[ERROR] " + err.message);
    loadStateEl && (loadStateEl.textContent = "error");
    term("[SVG] error: " + err.message);
    console.error(err);
  }
}

/* =========================
   BOOT SEQUENCE
   ========================= */
async function startBoot(){
  bootSet(0, "handshake");
  bootLine("[BOOT] initializing runtime…");
  await sleep(150);

  bootSet(12, "handshake");
  bootLine("[NET] link stable • encryption ok");
  await sleep(180);

  bootSet(25, "auth");
  bootLine("[AUTH] credentials verified • LS-07");
  await sleep(180);

  bootSet(40, "mount");
  bootLine("[FS] mounting local asset…");
  await sleep(180);

  bootSet(55, "request");
  bootLine("[SVG] requesting payload: map.svg");
  bootLine("[SVG] awaiting payload stream…", true);

  loadSvg();
}

// buttons
document.getElementById("btnClearTarget")?.addEventListener("click", () => {
  if(selectedEl) selectedEl.classList.remove("selected");
  selectedEl = null;
  clearDetails();
  term("[CLEAR] selection cleared");
});

document.getElementById("btnPin")?.addEventListener("click", () => {
  term("[PIN] area pinned to intel");
});

// initial live data
setTimeout(() => {
  fetchWeather();
  fetchNews();
  setInterval(fetchWeather, 300000);
  setInterval(fetchNews, 600000);
}, 1000);

// go
clearDetails();
startBoot();
  </script>'''
    
    # Replace the script section
    new_content = content[:script_start] + new_script + content[script_end:]
    
    # Write back
    with open('NEON CITY MAP.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('Script replaced successfully!')
else:
    print('Could not find script tags')