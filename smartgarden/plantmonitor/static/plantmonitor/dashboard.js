const charts = {};
const chartConfigs = [
  { id: 'moistureChart', label: 'Soil Moisture', key: 'soil_moisture' },
  { id: 'temperatureChart', label: 'Temperature', key: 'temperature' },
  { id: 'humidityChart', label: 'Humidity', key: 'humidity' },
  { id: 'lightChart', label: 'Light Level', key: 'light' },
  { id: 'reservoirChart', label: 'Reservoir Level', key: 'reservoir_level' }
];
function updateWithWarning(id, value, threshold, unit = '') {
    const el = document.getElementById(id + "Value");
    if (!el) return;
  
    let warning = '';
    if (!isNaN(value) && Number(value) < threshold) {
      warning = '<span style="color: red;">⚠ Needs Attention</span>';
    }
  
    el.innerHTML = `${value}${unit} ${warning}`;
  }
  
async function fetchLatest() {
  const res = await fetch('/api/latest/');
  return await res.json();
}

async function updateSensorValues() {
  const data = await fetchLatest();

  document.getElementById('temperatureValue').textContent = `${data.temperature}°C`;
  document.getElementById('humidityValue').textContent = `${data.humidity}%`;
  document.getElementById('lightValue').textContent = `${data.light} lx`;
  updateWithWarning("moisture", data.soil_moisture, moistureThreshold, '/ 1024');
  updateWithWarning("reservoir", data.reservoir_level, reservoirThreshold, '%');

  const plantStatus = document.getElementById('plantStatus');
  if (data.soil_moisture >= data.moisture_threshold) {
    plantStatus.innerHTML = "🌱 Plant is happy and healthy!";
  } else {
    plantStatus.innerHTML = "🥀 Plant is not happy!";
  }
}

async function fetchChartData() {
  const res = await fetch('/api/chart-data/');
  return await res.json();
}

async function updateCharts() {
  const data = await fetchChartData();
  chartConfigs.forEach(cfg => {
    const ctx = document.getElementById(cfg.id).getContext('2d');
    if (!charts[cfg.id]) {
      charts[cfg.id] = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.timestamps,
          datasets: [{
            label: cfg.label,
            data: data[cfg.key],
            borderColor: 'blue',
            borderWidth: 2,
            fill: false,
            tension: 0.3
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: { title: { display: true, text: 'Time' }},
            y: { beginAtZero: true }
          }
        }
      });
    } else {
      charts[cfg.id].data.labels = data.timestamps;
      charts[cfg.id].data.datasets[0].data = data[cfg.key];
      charts[cfg.id].update();
    }
  });
}

function openPresetModal() {
  document.getElementById('presetModal').style.display = 'flex';
}
function closePresetModal() {
  document.getElementById('presetModal').style.display = 'none';
}
function toggleTrend(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'block' ? 'none' : 'block';
}
function checkConnection() {
  const isConnected = true;
  if (!isConnected) {
    document.getElementById("pumpMessage").innerText = "❌ Not connected to plant system.";
    return false;
  }
  setTimeout(() => {
    document.getElementById("pumpMessage").innerText = "✅ Pump turned on!";
    setTimeout(() => {
      document.getElementById("pumpMessage").innerText = "";
    }, 5000);
  }, 500);
  return true;
}

// ⏱ Refresh logic
setInterval(updateSensorValues, 1000);
setInterval(updateCharts, 180000);
updateSensorValues();
updateCharts();