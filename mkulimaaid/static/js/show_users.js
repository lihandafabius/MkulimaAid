document.addEventListener("DOMContentLoaded", () => {
  const chartContainer = document.getElementById("pieChartsContainer");
  const timeFilterLinks = document.querySelectorAll('.dropdown-menu a[data-filter]');

  // Function to fetch and render the stacked bar chart for crop diseases by location
  function loadCropDiseasesByLocation(filter = "week") {
    fetch(`/api/crop-diseases-by-location?filter=${filter}`)
      .then((response) => response.json())
      .then((data) => {
        // Clear existing chart
        chartContainer.innerHTML = "";

        // Initialize data for the chart
        let diseases = [];
        let locations = [];
        let datasets = [];
        let diseaseLocationCounts = {};

        // Process the data to organize it into a format suitable for a stacked bar chart
        data.forEach((locationData) => {
          const { location, diseases: locationDiseases } = locationData;
          if (!locations.includes(location)) locations.push(location);

          locationDiseases.forEach((disease) => {
            if (!diseases.includes(disease.name)) diseases.push(disease.name);
            if (!diseaseLocationCounts[disease.name]) {
              diseaseLocationCounts[disease.name] = {};
            }
            diseaseLocationCounts[disease.name][location] = disease.count;
          });
        });

        // Create a container for the chart
        const locationDiv = document.createElement("div");
        locationDiv.style.margin = "20px";
        locationDiv.style.textAlign = "center";

        // Create a canvas for the chart
        const canvas = document.createElement("canvas");
        canvas.width = 500;
        canvas.height = 500;
        locationDiv.appendChild(canvas);

        // Append the container to the main container
        chartContainer.appendChild(locationDiv);

        // Prepare chart datasets for each disease
        diseases.forEach((diseaseName) => {
          let diseaseCounts = locations.map((location) => diseaseLocationCounts[diseaseName][location] || 0);

          datasets.push({
            label: diseaseName,
            data: diseaseCounts,
            backgroundColor: getRandomColor(), // You can define a function to generate random colors for each disease
            stack: "stack1",
          });
        });

        // Prepare chart data
        const chartData = {
          labels: locations,  // Locations on the x-axis
          datasets: datasets, // Datasets for each disease
        };

        // Render the stacked bar chart
        new Chart(canvas, {
          type: "bar",
          data: chartData,
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: true,
                position: "top",
              },
            },
            scales: {
              x: {
                stacked: true,
                title: {
                  display: true,
                  text: "Location",
                },
              },
              y: {
                stacked: true,
                title: {
                  display: true,
                  text: "Occurrences",
                },
              },
            },
          },
        });
      })
      .catch((error) => console.error("Error fetching crop diseases data:", error));
  }

  // Function to generate a random color for each disease
  function getRandomColor() {
    const letters = "0123456789ABCDEF";
    let color = "#";
    for (let i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }

  // Attach event listeners to the dropdown filter links
  timeFilterLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const filter = event.target.getAttribute("data-filter");
      loadCropDiseasesByLocation(filter);
    });
  });

  // Initial load with default filter (week)
  loadCropDiseasesByLocation("week");
});
