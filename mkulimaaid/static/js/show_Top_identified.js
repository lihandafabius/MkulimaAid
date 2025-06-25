document.addEventListener("DOMContentLoaded", () => {
  const cropChartContainer = document.getElementById('topCropDiseasesChart').getContext('2d');
  const userChartContainer = document.getElementById('usersJoinedChart').getContext('2d');
  const timeFilterLabel = document.getElementById('timeFilterLabel');

  let topCropDiseasesChart = null;
  let usersJoinedChart = null;

  // Fetch and render the crop diseases data
  function loadCropData(filter = 'all') {
    fetch(`/api/top-crop-diseases?filter=${filter}`)
      .then(response => response.json())
      .then(data => {
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
              backgroundColor: 'rgba(75, 192, 75, 0.2)',
              borderColor: 'rgba(34, 139, 34, 1)',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: 'Detections' }
              },
              x: {
                title: { display: true, text: 'Crop Diseases' }
              }
            },
            plugins: {
              legend: { display: true, position: 'top' },
              tooltip: {
                backgroundColor: 'rgba(75, 192, 75, 0.9)',
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                callbacks: {
                  label: ctx => `${ctx.raw} Detections`
                }
              }
            }
          }
        });
      })
      .catch(error => console.error(`Error fetching crop data for ${filter}:`, error));
  }

  // Fetch and render the users joined data
  function loadUserData(filter = 'all') {
    fetch(`/api/users-joined?filter=${filter}`)
      .then(response => response.json())
      .then(data => {
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
              backgroundColor: 'rgba(75, 192, 75, 0.2)',
              borderColor: 'rgba(34, 139, 34, 1)',
              borderWidth: 2,
              tension: 0.4
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: 'Number of Users' }
              },
              x: {
                title: { display: true, text: 'Date' }
              }
            },
            plugins: {
              legend: { display: true, position: 'top' },
              tooltip: {
                backgroundColor: 'rgba(75, 192, 75, 0.9)',
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                callbacks: {
                  label: ctx => `${ctx.raw} Users`
                }
              }
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
        loadCropData(filter);
        loadUserData(filter);
        timeFilterLabel.innerText = event.target.textContent;
      }
    });
  });

  // Initial load with default filter (all-time)
  loadCropData('all');
  loadUserData('all');
});
