document.addEventListener("DOMContentLoaded", () => {
  const chartContainer = document.getElementById("pieChartsContainer");
  const timeFilterLinks = document.querySelectorAll('.dropdown-menu a[data-filter]');

  // Function to fetch and render the data in an interactive table
  function loadCropDiseasesByLocation(filter = "all") {
    fetch(`/api/crop-diseases-by-location?filter=${filter}`)
      .then((response) => response.json())
      .then((data) => {
        // Clear existing content
        chartContainer.innerHTML = "";

        // Create the table
        const table = document.createElement("table");
        table.classList.add("table", "table-bordered", "table-hover", "display");
        table.id = "interactiveTable"; // Assign an ID for DataTables initialization

        // Create the table header
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        const headers = ["Location", "Diseases (with Counts)"];
        headers.forEach((header) => {
          const th = document.createElement("th");
          th.textContent = header;
          headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create the table body
        const tbody = document.createElement("tbody");

        // Populate table rows with grouped data
        data.forEach((locationData) => {
          const { location, diseases: locationDiseases } = locationData;

          const row = document.createElement("tr");

          const locationCell = document.createElement("td");
          locationCell.textContent = location;
          row.appendChild(locationCell);

          const diseasesCell = document.createElement("td");
          // Format diseases with counts as "Disease Name (Count)"
          const diseasesList = locationDiseases
            .map((disease) => `${disease.name} (${disease.count})`)
            .join(", ");
          diseasesCell.textContent = diseasesList;
          row.appendChild(diseasesCell);

          tbody.appendChild(row);
        });

        table.appendChild(tbody);
        chartContainer.appendChild(table);

        // Initialize DataTables
        $(document).ready(function () {
          $('#interactiveTable').DataTable({
            paging: true,            // Enable pagination
            searching: true,         // Enable search box
            ordering: true,          // Enable column sorting
            responsive: true,        // Make the table responsive
            info: true,              // Show table info
            lengthChange: true,      // Allow changing the number of rows displayed
          });
        });
      })
      .catch((error) => console.error("Error fetching crop diseases data:", error));
  }

  // Attach event listeners to the dropdown filter links
  timeFilterLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const filter = event.target.getAttribute("data-filter");
      loadCropDiseasesByLocation(filter);
    });
  });

  // Initial load with default filter (month)
  loadCropDiseasesByLocation("all");
});
