document.addEventListener("DOMContentLoaded", () => {
  const chartContainer = document.getElementById("diseaseConfidenceChart");

  // Function to fetch disease confidence data and render a donut chart
  function loadDiseaseConfidenceChart() {
    fetch('/api/disease-confidence')
      .then(response => response.json())
      .then(data => {
        // Extract data for the chart
        const labels = data.map(item => item.disease_name);
        const values = data.map(item => item.avg_confidence);

        // Generate random colors for each disease
        const colors = labels.map(() => getRandomColor());

        // Prepare chart data
        const chartData = {
          labels: labels,
          datasets: [{
            data: values,
            backgroundColor: colors,
            borderWidth: 1
          }]
        };

        // Render the donut chart
        new Chart(chartContainer, {
          type: 'doughnut', // Use 'doughnut' for a donut chart
          data: chartData,
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false // Hide legend
              },
              tooltip: {
                callbacks: {
                  label: (tooltipItem) => {
                    const percentage = tooltipItem.raw;
                    return `${tooltipItem.label}: ${percentage.toFixed(2)}%`;
                  }
                }
              },
              datalabels: {
                color: '#fff', // Label text color
                formatter: (value) => `${value.toFixed(1)}%`, // Show percentage inside slices
                font: {
                  size: 14
                }
              }
            },
            cutout: '70%', // Adjust to make it look like a donut
            layout: {
              padding: 20
            }
          }
        });
      })
      .catch(error => console.error("Error fetching disease confidence data:", error));
  }

  // Function to generate a random color
  function getRandomColor() {
    const letters = "0123456789ABCDEF";
    let color = "#";
    for (let i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }

  // Load the chart
  loadDiseaseConfidenceChart();
});
