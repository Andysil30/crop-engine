// Locally (port 5500) talk to port 8000. Online, use the same address.
const API = location.port === "5500" ? "http://127.0.0.1:8000" : "";
let T = {};            // current translations
let lastResult = null; // so we can redraw when language changes
let chart = null;

const $ = (id) => document.getElementById(id);

async function loadLang(lang) {
  const res = await fetch(`i18n/${lang}.json`);
  T = await res.json();
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = T[el.dataset.i18n] || el.dataset.i18n;
  });
  localStorage.setItem("lang", lang);
  if (lastResult) render(lastResult);
}

async function getWeather() {
  const city = $("city").value.trim();
  if (!city) return;
  try {
    const res = await fetch(`${API}/weather?city=${encodeURIComponent(city)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    $("temperature").value = data.temperature;
    $("humidity").value = data.humidity;
    $("weatherMsg").textContent = `${T.weather_ok} ${data.rain_forecast_5d_mm} mm`;
  } catch (e) {
    $("weatherMsg").textContent = e.message;
  }
}

async function predict() {
  $("error").textContent = "";
  const body = {};
  for (const id of ["N", "P", "K", "ph", "temperature", "humidity", "rainfall"]) {
    const v = $(id).value;
    if (v === "") { $("error").textContent = T.error; return; }
    body[id] = Number(v);
  }
  try {
    const res = await fetch(`${API}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("bad request");
    lastResult = { data: await res.json(), input: body };
    render(lastResult);
  } catch (e) {
    $("error").textContent = T.error;
  }
}

function render({ data, input }) {
  const box = $("results");
  box.innerHTML = `<h2>${T.top3}</h2>`;

  data.recommendations.forEach((rec, i) => {
    const f = rec.fertilizer;
    const rows = f.nutrients.map(n => {
      const advice = n.products.length
        ? `<ul>${n.products.map(p => `<li>${T.add} ${p.amount} ${T.kg} ${p.name}</li>`).join("")}</ul>`
        : "";
      return `<li><b>${n.nutrient}</b>: ${T.your_value} ${n.your_value}, ${T.ideal_value} ${n.ideal_value}
        <span class="badge ${n.status}">${T["status_" + n.status]}</span>${advice}</li>`;
    }).join("");

    box.innerHTML += `
      <div class="card crop">
        <h3>${i + 1}. ${rec.crop} (${T.confidence}: ${rec.confidence}%)</h3>
        <h4>${T.fertilizer_plan}</h4>
        <ul>${rows}</ul>
        <p>pH: ${T[f.ph.advice]}</p>
        ${i === 0 ? `<h4>${T.chart_title} ${rec.crop}</h4><canvas id="chart"></canvas>` : ""}
      </div>`;
  });

  drawChart(data.recommendations[0], input);
}

function drawChart(rec, input) {
  const nutrients = rec.fertilizer.nutrients;
  if (chart) chart.destroy();
  chart = new Chart($("chart"), {
    type: "bar",
    data: {
      labels: nutrients.map(n => n.nutrient),
      datasets: [
        { label: T.your_value, data: nutrients.map(n => n.your_value), backgroundColor: "#d9822b" },
        { label: T.ideal_value, data: nutrients.map(n => n.ideal_value), backgroundColor: "#2e7d32" },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
}

$("weatherBtn").addEventListener("click", getWeather);
$("predictBtn").addEventListener("click", predict);
$("lang").addEventListener("change", e => loadLang(e.target.value));

const saved = localStorage.getItem("lang") || "en";
$("lang").value = saved;
loadLang(saved);
// Register the helper that makes the app installable
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js").catch(() => {});
}