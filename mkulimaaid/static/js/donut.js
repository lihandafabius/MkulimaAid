document.addEventListener("DOMContentLoaded", () => {
  const ctx = document
    .getElementById("diseaseConfidenceChart")
    .getContext("2d");

  fetch("/api/disease-confidence")
    .then((res) => res.json())
    .then((raw) => {
      const uniformFillColor = "rgba(75, 192, 75, 0.5)";    // bubble fill
      const borderGreen = "rgba(34, 139, 34, 1)";           // bubble border

      const bubbles = raw.map(({ disease_name, avg_confidence }, i) => {
        let conf = parseFloat(avg_confidence);
        if (conf <= 1) conf *= 100;
        if (conf > 100) conf = 100;

        return {
          x: i,
          y: conf,
          r: Math.max(6, conf / 8),
          backgroundColor: uniformFillColor,
          borderColor: borderGreen,
          borderWidth: 1,
          disease: disease_name,
          confidence: conf
        };
      });

      new Chart(ctx, {
        type: "bubble",
        data: {
          datasets: [{
            label: "Disease confidence",
            data: bubbles,
            backgroundColor: uniformFillColor,
            borderColor: borderGreen,
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "rgba(75, 192, 75, 0.9)",
              titleColor: "#ffffff",
              bodyColor: "#ffffff",
              callbacks: {
                label: (ctx) => {
                  const d = ctx.raw;
                  return `${d.disease}: ${d.confidence.toFixed(2)}%`;
                }
              }
            }
          },
          scales: {
            x: {
              type: "linear",
              title: {
                display: true,
                text: "Disease Index"
              },
              ticks: { precision: 0 } // removed color
              // grid: uses default
            },
            y: {
              title: {
                display: true,
                text: "Confidence (%)"
              },
              suggestedMin: 0,
              suggestedMax: 100,
              ticks: {
                callback: (v) => `${v}%`
              }
              // grid: uses default
            }
          }
        }
      });
    })
    .catch((err) =>
      console.error("Error fetching disease confidence data:", err)
    );
});
