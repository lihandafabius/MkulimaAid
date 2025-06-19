document.addEventListener("DOMContentLoaded", () => {
  const chartContainer = document.getElementById("diseaseConfidenceChart");

  // Fallback if the chart container is a <canvas>
  const ctx = chartContainer.getContext ? chartContainer.getContext("2d") : null;

  function generateGreenShades(count) {
    const shades = [];
    for (let i = 0; i < count; i++) {
      const greenValue = 150 + (i * (105 / count)); // 150–255 range
      shades.push(`rgba(75, ${Math.floor(greenValue)}, 75, 0.7)`);
    }
    return shades;
  }

  function loadDiseaseConfidenceChart() {
    fetch('/api/disease-confidence')
      .then(response => response.json())
      .then(data => {
        const labels = data.map(item => item.disease_name);
        const values = data.map(item => item.avg_confidence);
        const colors = generateGreenShades(labels.length);

        if (!ctx) {
          console.error("Chart context not found. Ensure #diseaseConfidenceChart is a <canvas> element.");
          return;
        }

        new Chart(ctx, {
          type: 'polarArea',
          data: {
            labels: labels,
            datasets: [{
              label: 'Average Confidence (%)',
              data: values,
              backgroundColor: colors,
              borderColor: '#ffffff',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'right',
                labels: {
                  color: '#2e7d32'
                }
              },
              tooltip: {
                callbacks: {
                  label: (ctx) => `${ctx.label}: ${ctx.raw.toFixed(2)}%`
                }
              }
            },
            scales: {
              r: {
                angleLines: { display: true },
                suggestedMin: 0,
                suggestedMax: 100,
                ticks: {
                  callback: val => `${val}%`,
                  color: '#1b5e20'
                },
                grid: {
                  color: '#e0f2f1'
                }
              }
            }
          }
        });
      })
      .catch(error => console.error("Error fetching disease confidence data:", error));
  }

  loadDiseaseConfidenceChart();
});
