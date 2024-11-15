
document.addEventListener("DOMContentLoaded", () => {
  const cropChartContainer = document.getElementById('topCropDiseasesChart').getContext('2d');
  const userChartContainer = document.getElementById('usersJoinedChart').getContext('2d');

  let topCropDiseasesChart = null;
  let usersJoinedChart = null;

  /**
   * Fetch and render the crop diseases data
   */
  function loadCropData(filter = 'week') {
    fetch(`/api/top-crop-diseases?filter=${filter}`)
      .then(response => response.json())
      .then(data => {
        const labels = data.map(item => item.name);
        const counts = data.map(item => item.count);

        if (topCropDiseasesChart) topCropDiseasesChart.destroy();

        topCropDiseasesChart = new Chart(cropChartContainer, {
          type: 'bar',
          data: {
            labels: labels,
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
      .catch(error => console.error('Error fetching crop data:', error));
  }

  /**
   * Fetch and render the users joined data with trendline
   */
  function loadUserData(filter = 'week') {
    fetch(`/api/users-joined?filter=${filter}`)
      .then(response => response.json())
      .then(data => {
        const labels = data.map(item => item.date);
        const counts = data.map(item => item.count);

        if (usersJoinedChart) usersJoinedChart.destroy();

        usersJoinedChart = new Chart(userChartContainer, {
          type: 'line',
          data: {
            labels: labels,
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
      .catch(error => console.error('Error fetching user data:', error));
  }

  // Load initial data with the 'week' filter
  loadCropData('week');
  loadUserData('week');

  // Handle time filter changes
  document.querySelector('.dropdown-menu').addEventListener('click', event => {
    const filter = event.target.getAttribute('data-filter');
    if (filter) {
      loadCropData(filter);
      loadUserData(filter);
      document.getElementById('timeFilterLabel').innerText = event.target.textContent;
    }
  });
});

