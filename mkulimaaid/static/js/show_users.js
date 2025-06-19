document.addEventListener("DOMContentLoaded", () => {
  const chartContainer = document.getElementById("pieChartsContainer");
  const timeFilterLinks = document.querySelectorAll('.dropdown-menu a[data-filter]');

  function loadCropDiseasesByLocation(filter = "all") {
    fetch(`/api/crop-diseases-by-location?filter=${filter}`)
      .then((response) => response.json())
      .then((data) => {
        chartContainer.innerHTML = "";

        const table = document.createElement("table");
        table.classList.add("table", "table-bordered", "table-hover", "display");
        table.id = "interactiveTable";

        // Create table header
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        const headers = ["Location", "Diseases (with Counts)"];
        headers.forEach((header) => {
          const th = document.createElement("th");
          th.textContent = header;
          th.setAttribute("style", `
            background-color: #d4edda;
            color: #155724;
            padding: 10px;
            text-align: left;
          `);
          headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement("tbody");

        data.forEach((locationData, index) => {
          const { location, diseases: locationDiseases } = locationData;
          const row = document.createElement("tr");

          row.setAttribute("style", `
            background-color: ${index % 2 === 0 ? "#f0fdf4" : "#e6ffe6"};
          `);

          const locationCell = document.createElement("td");
          locationCell.textContent = location;
          locationCell.setAttribute("style", `
            color: #1b5e20;
            padding: 8px;
          `);
          row.appendChild(locationCell);

          const diseasesCell = document.createElement("td");
          const diseasesList = locationDiseases
            .map((disease) => `${disease.name} (${disease.count})`)
            .join(", ");
          diseasesCell.textContent = diseasesList;
          diseasesCell.setAttribute("style", `
            color: #2e7d32;
            padding: 8px;
          `);
          row.appendChild(diseasesCell);

          tbody.appendChild(row);
        });

        table.appendChild(tbody);
        chartContainer.appendChild(table);

        // Initialize DataTables with 5 entries default and 5 in dropdown
        $(document).ready(function () {
          $('#interactiveTable').DataTable({
            paging: true,
            searching: true,
            ordering: true,
            responsive: true,
            info: true,
            lengthChange: true,
            pageLength: 5,
            lengthMenu: [5, 10, 25, 50, 100],
            language: {
              searchPlaceholder: "Search by location or disease...",
              search: ""
            }
          });
        });
      })
      .catch((error) => console.error("Error fetching crop diseases data:", error));
  }

  // Dropdown filter links
  timeFilterLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const filter = event.target.getAttribute("data-filter");
      loadCropDiseasesByLocation(filter);
    });
  });

  // Load default view
  loadCropDiseasesByLocation("all");
});
