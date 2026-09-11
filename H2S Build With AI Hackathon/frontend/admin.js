const API_BASE = "http://localhost:8000";

async function loadDashboard() {
  const stats = await fetch(`${API_BASE}/api/dashboard-stats`).then((r) => r.json());
  document.getElementById("statTotal").textContent = stats.total_complaints;
  document.getElementById("statUrgency").textContent = stats.average_urgency;
  document.getElementById("statStates").textContent = Object.keys(stats.state_breakdown).length;

  new Chart(document.getElementById("categoryChart"), {
    type: "bar",
    data: {
      labels: Object.keys(stats.category_breakdown),
      datasets: [{
        label: "Complaints",
        data: Object.values(stats.category_breakdown),
        backgroundColor: "#4f7cff",
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });

  const hotspots = await fetch(`${API_BASE}/api/hotspots`).then((r) => r.json());

  const map = L.map("map").setView([22.9734, 78.6569], 4.5); // center of India
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  hotspots.forEach((h) => {
    if (h.latitude && h.longitude) {
      const radius = Math.min(8 + h.complaint_count * 2, 30);
      L.circleMarker([h.latitude, h.longitude], {
        radius,
        color: h.total_priority_score > 100 ? "#e63946" : "#f4a261",
        fillOpacity: 0.6,
      })
        .bindPopup(`<b>${h.district}, ${h.state}</b><br>${h.complaint_count} complaints<br>${h.recommendation}`)
        .addTo(map);
    }
  });

  const listEl = document.getElementById("hotspotList");
  listEl.innerHTML = hotspots
    .slice(0, 10)
    .map(
      (h) => `
    <div class="hotspot-item">
      <div class="hotspot-header">
        <strong>${h.district}, ${h.state}</strong>
        <span class="badge">${h.complaint_count} reports</span>
        <span class="badge priority">Score: ${h.total_priority_score}</span>
      </div>
      <p class="recommendation">${h.recommendation}</p>
    </div>
  `
    )
    .join("");
}

loadDashboard();