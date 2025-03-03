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

        // Use a predefined color palette for consistency
        const colors = [
          "#4CAF50", "#FF9800", "#03A9F4", "#E91E63", "#9C27B0",
          "#FF5722", "#009688", "#795548", "#607D8B", "#CDDC39"
        ];

        // Prepare chart data
        const chartData = {
          labels: labels,
          datasets: [{
            data: values,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 1
          }]
        };

        // Render the donut chart
        new Chart(chartContainer, {
          type: 'doughnut',
          data: chartData,
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false // Hide default legend to keep UI clean
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
                color: '#fff', // White labels for better contrast
                anchor: 'center',
                align: 'center',
                formatter: (value) => `${value.toFixed(1)}%`,
                font: {
                  size: 13,
                  weight: 'bold'
                }
              }
            },
            cutout: '65%', // Adjust the hole size for better aesthetics
            layout: {
              padding: 10
            }
          }
        });
      })
      .catch(error => console.error("Error fetching disease confidence data:", error));
  }

  // Load the chart
  loadDiseaseConfidenceChart();
});
