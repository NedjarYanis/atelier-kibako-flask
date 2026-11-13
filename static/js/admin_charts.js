/**
 * Atelier Kibako — Télémétrie Atelier (Chart.js + /api/v1/telemetry)
 */
(async function () {
  const woodCanvas = document.getElementById("chart-wood-stock");
  const catCanvas = document.getElementById("chart-categories");
  if (!woodCanvas || !catCanvas || !window.Chart) return;

  try {
    const res = await fetch("/api/v1/telemetry");
    const data = await res.json();
    if (!data.ok) return;

    const palette = [
      "#9e472a",
      "#b8863b",
      "#3f6249",
      "#5a5047",
      "#c98448",
      "#2d4a53",
      "#7c4d3a",
      "#84786c",
    ];

    new window.Chart(woodCanvas, {
      type: "bar",
      data: {
        labels: data.wood_stock.labels,
        datasets: [
          {
            label: "Unités en stock",
            data: data.wood_stock.values,
            backgroundColor: palette,
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });

    new window.Chart(catCanvas, {
      type: "doughnut",
      data: {
        labels: data.categories.labels,
        datasets: [
          {
            data: data.categories.values,
            backgroundColor: palette,
            borderWidth: 2,
            borderColor: "#fffdf9",
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
        },
      },
    });
  } catch (err) {
    console.warn("Télémétrie Chart.js indisponible:", err);
  }
})();
