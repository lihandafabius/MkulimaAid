document.addEventListener("DOMContentLoaded", () => {
  const cropChartContainer = document.getElementById('topCropDiseasesChart').getContext('2d');
  const userChartContainer = document.getElementById('usersJoinedChart').getContext('2d');
  const timeFilterLabel = document.getElementById('timeFilterLabel');

  let topCropDiseasesChart = null;
  let usersJoinedChart = null;

  // Fetch and render the crop diseases data
  function loadCropData(filter = 'month') {
    console.log(`Fetching crop data for filter: ${filter}`);
    fetch(`/api/top-crop-diseases?filter=${filter}`)
      .then(response => response.json())
      .then(data => {
        console.log(`Crop data received for ${filter}:`, data);

        const labels = data.map(item => item.name);
        const counts = data.map(item => item.count);

        if (topCropDiseasesChart) {
          topCropDiseasesChart.destroy();
          topCropDiseasesChart = null;
        }

        topCropDiseasesChart = new Chart(cropChartContainer, {
          type: 'bar',
          data: {
            labels,
            datasets: [{
              label: 'Number of Detections',
              data: counts,
              backgroundColor: 'rgba(54, 162, 235, 0.6)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: { beginAtZero: true, title: { display: true, text: 'Detections' } },
              x: { title: { display: true, text: 'Crop Diseases' } }
            },
            plugins: { legend: { display: true, position: 'top' } }
          }
        });
      })
      .catch(error => console.error(`Error fetching crop data for ${filter}:`, error));
  }

  // Fetch and render the users joined data
  function loadUserData(filter = 'month') {
    console.log(`Fetching user data for filter: ${filter}`);
    fetch(`/api/users-joined?filter=${filter}`)
      .then(response => response.json())
      .then(data => {
        console.log(`User data received for ${filter}:`, data);

        const labels = data.map(item => item.date);
        const counts = data.map(item => item.count);

        if (usersJoinedChart) {
          usersJoinedChart.destroy();
          usersJoinedChart = null;
        }

        usersJoinedChart = new Chart(userChartContainer, {
          type: 'line',
          data: {
            labels,
            datasets: [{
              label: 'Users Joined',
              data: counts,
              fill: true,
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 2,
              tension: 0.4
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: { beginAtZero: true, title: { display: true, text: 'Number of Users' } },
              x: { title: { display: true, text: 'Date' } }
            },
            plugins: {
              legend: { display: true, position: 'top' },
              tooltip: { callbacks: { label: ctx => `${ctx.raw} Users` } }
            }
          }
        });
      })
      .catch(error => console.error(`Error fetching user data for ${filter}:`, error));
  }

  // Handle dropdown filter changes
  document.querySelectorAll('.dropdown-menu a[data-filter]').forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      const filter = event.target.getAttribute('data-filter');
      if (filter) {
        console.log(`Applying filter: ${filter}`);
        loadCropData(filter);
        loadUserData(filter);
        timeFilterLabel.innerText = event.target.textContent;
      }
    });
  });

  // Initial load with default filter (month)
  loadCropData('month');
  loadUserData('month');
});
