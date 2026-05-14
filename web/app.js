const GROUP_ORDER = ["Performa mesin", "Dimensi kendaraan", "Efisiensi & bobot"];

const els = {
  form: document.querySelector("#prediction-form"),
  groups: document.querySelector("#feature-groups"),
  resultState: document.querySelector("#result-state"),
  resultPanel: document.querySelector("#result-panel"),
  predictionThousand: document.querySelector("#prediction-thousand"),
  predictionUsd: document.querySelector("#prediction-usd"),
  predictionRange: document.querySelector("#prediction-range"),
  inputJson: document.querySelector("#input-json"),
  salesChart: document.querySelector("#sales-chart"),
  topSalesBody: document.querySelector("#top-sales-body"),
  metrics: document.querySelector("#metrics"),
  studentName: document.querySelector("#student-name"),
  studentMeta: document.querySelector("#student-meta"),
  predictButton: document.querySelector("#predict-button"),
  submitStatus: document.querySelector("#submit-status"),
};

let metadata = null;

function formatNumber(value, digits = 3) {
  return Number(value).toLocaleString("id-ID", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatUsd(value) {
  return Number(value).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

function decimalDigitsFor(feature) {
  return Number(feature.step) < 1 ? 3 : 1;
}

function formatInputValue(value, feature) {
  return Number(value).toFixed(decimalDigitsFor(feature)).replace(".", ",");
}

function parseLocalizedNumber(value, label) {
  const raw = String(value ?? "").trim();
  if (!raw) {
    throw new Error(`${label} wajib diisi.`);
  }
  const normalized = raw.includes(",") ? raw.replace(/\./g, "").replace(",", ".") : raw;
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed)) {
    throw new Error(`${label} harus berupa angka, contoh 3,5 atau 3.5.`);
  }
  return parsed;
}

function featureRangeText(feature) {
  return `Rentang ${formatInputValue(feature.min, feature)}–${formatInputValue(feature.max, feature)} ${feature.unit}`;
}

function setFieldState(input, message = "") {
  const wrapper = input.closest(".field");
  const error = wrapper?.querySelector(".field-error");
  input.classList.toggle("is-invalid", Boolean(message));
  input.setAttribute("aria-invalid", message ? "true" : "false");
  if (error) {
    error.textContent = message;
  }
}

function validateFieldInput(input, feature) {
  const parsed = parseLocalizedNumber(input.value, feature.label);
  if (parsed < feature.min || parsed > feature.max) {
    throw new Error(`${feature.label} harus di antara ${formatInputValue(feature.min, feature)} dan ${formatInputValue(feature.max, feature)}.`);
  }
  return parsed;
}

function createField(feature) {
  const wrapper = document.createElement("div");
  wrapper.className = "field";

  const label = document.createElement("label");
  label.htmlFor = feature.name;
  label.textContent = feature.label;

  const input = document.createElement("input");
  input.id = feature.name;
  input.name = feature.name;
  input.type = "text";
  input.dataset.min = feature.min;
  input.dataset.max = feature.max;
  input.dataset.step = feature.step;
  input.value = formatInputValue(feature.default, feature);
  input.required = true;
  input.inputMode = "decimal";
  input.autocomplete = "off";
  input.setAttribute("aria-describedby", `${feature.name}-hint ${feature.name}-error`);
  input.addEventListener("blur", () => {
    try {
      input.value = formatInputValue(validateFieldInput(input, feature), feature);
      setFieldState(input);
    } catch (error) {
      setFieldState(input, error.message);
    }
  });

  const hint = document.createElement("span");
  hint.id = `${feature.name}-hint`;
  hint.className = "field-hint";
  hint.textContent = featureRangeText(feature);

  const error = document.createElement("span");
  error.id = `${feature.name}-error`;
  error.className = "field-error";

  wrapper.append(label, input, hint, error);
  return wrapper;
}

function renderFeatureForm(features) {
  els.groups.innerHTML = "";
  for (const groupName of GROUP_ORDER) {
    const groupFeatures = features.filter((feature) => feature.group === groupName);
    const section = document.createElement("section");
    section.className = "feature-group";

    const heading = document.createElement("h3");
    heading.textContent = groupName;

    const grid = document.createElement("div");
    grid.className = "field-grid";
    groupFeatures.forEach((feature) => grid.appendChild(createField(feature)));

    section.append(heading, grid);
    els.groups.appendChild(section);
  }
}

function renderSalesChart(rows) {
  const maxSales = Math.max(...rows.map((row) => row.sales));
  const chartWidth = 720;
  const rowHeight = 36;
  const labelWidth = 150;
  const valueWidth = 72;
  const barWidth = chartWidth - labelWidth - valueWidth - 32;
  const chartHeight = rows.length * rowHeight + 16;
  const palette = ["#3b82f6", "#2563eb", "#1d4ed8", "#64748b"];

  const bars = rows
    .map((row, index) => {
      const y = 12 + index * rowHeight;
      const width = Math.max(4, (row.sales / maxSales) * barWidth);
      const color = palette[index % palette.length];
      return `
        <g class="chart-bar" data-rank="${row.rank}">
          <text x="0" y="${y + 18}" class="chart-label">${row.rank}. ${row.car}</text>
          <rect x="${labelWidth}" y="${y}" width="${barWidth}" height="22" rx="6" class="chart-track"></rect>
          <rect x="${labelWidth}" y="${y}" width="${width}" height="22" rx="6" fill="${color}"></rect>
          <text x="${labelWidth + barWidth + 12}" y="${y + 17}" class="chart-value">${formatNumber(row.sales, 1)}</text>
        </g>
      `;
    })
    .join("");

  els.salesChart.innerHTML = `
    <svg class="sales-svg" viewBox="0 0 ${chartWidth} ${chartHeight}" role="img" aria-label="Chart 10 mobil dengan penjualan tertinggi">
      ${bars}
    </svg>
  `;
}

function renderTopSales(rows) {
  els.topSalesBody.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${row.rank}</td>
          <td>${row.car}</td>
          <td>${formatNumber(row.sales, 3)}</td>
          <td>${formatNumber(row.price, 3)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderMetrics(model) {
  const items = [
    ["Model", model.name],
    ["Target", model.target],
    ["Training/testing", `${model.trainRows}/${model.testRows} baris`],
    ["RMSE test", formatNumber(model.metrics.RMSE, 3)],
    ["R2 Score test", formatNumber(model.metrics["R2 Score"], 3)],
  ];
  els.metrics.innerHTML = items
    .map(([label, value]) => `<div class="metric-item"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function collectPayload() {
  const payload = {};
  for (const feature of metadata.features) {
    const input = els.form.elements[feature.name];
    try {
      const parsed = validateFieldInput(input, feature);
      setFieldState(input);
      payload[feature.name] = parsed;
    } catch (error) {
      setFieldState(input, error.message);
      throw error;
    }
  }
  return payload;
}

function showError(message) {
  els.resultState.hidden = false;
  els.resultState.style.display = "grid";
  els.resultState.setAttribute("aria-hidden", "false");
  els.resultPanel.hidden = true;
  els.resultPanel.style.display = "none";
  els.resultPanel.setAttribute("aria-hidden", "true");
  els.resultState.classList.add("error-box");
  els.resultState.innerHTML = `<strong>Prediksi gagal.</strong><span>${message}</span>`;
  els.submitStatus.textContent = "Prediksi gagal. Cek nilai input.";
}

function showPrediction(data) {
  els.resultState.hidden = true;
  els.resultState.style.display = "none";
  els.resultState.setAttribute("aria-hidden", "true");
  els.resultPanel.hidden = false;
  els.resultPanel.style.display = "grid";
  els.resultPanel.setAttribute("aria-hidden", "false");
  els.resultState.classList.remove("error-box");
  els.predictionThousand.textContent = formatNumber(data.prediction, 3);
  els.predictionUsd.textContent = formatUsd(data.predictionUsd);
  els.predictionRange.textContent = `Rentang kasar berbasis RMSE: ${formatNumber(data.estimatedRange.lower, 3)}–${formatNumber(data.estimatedRange.upper, 3)} ribu USD`;
  els.inputJson.textContent = JSON.stringify(data.input, null, 2);
  els.submitStatus.textContent = "Prediksi berhasil dihitung dari nilai form saat ini.";
}

async function loadMetadata() {
  const response = await fetch("/api/metadata");
  if (!response.ok) {
    throw new Error(`metadata HTTP ${response.status}`);
  }
  metadata = await response.json();

  els.studentName.textContent = metadata.student.name;
  els.studentMeta.textContent = `NPM ${metadata.student.npm} · ${metadata.student.class}`;
  renderFeatureForm(metadata.features);
  renderSalesChart(metadata.topSales);
  renderTopSales(metadata.topSales);
  renderMetrics(metadata.model);
}

async function submitPrediction(event) {
  event.preventDefault();
  els.predictButton.disabled = true;
  els.predictButton.textContent = "Menghitung...";
  els.submitStatus.textContent = "Mengirim input ke model LinearRegression...";
  let payload;
  try {
    payload = collectPayload();
  } catch (error) {
    const invalidInput = els.form.querySelector(".is-invalid");
    invalidInput?.focus();
    throw error;
  }
  const response = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `predict HTTP ${response.status}`);
  }

  showPrediction(await response.json());
}

els.form.addEventListener("submit", (event) => {
  submitPrediction(event)
    .catch((error) => showError(error.message))
    .finally(() => {
      els.predictButton.disabled = false;
      els.predictButton.textContent = "Hitung prediksi";
    });
});

loadMetadata().catch((error) => {
  els.groups.innerHTML = `<div class="empty-state error-box"><strong>Data app gagal dimuat.</strong><span>${error.message}</span></div>`;
});
