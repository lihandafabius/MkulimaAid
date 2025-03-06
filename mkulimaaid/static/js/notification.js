document.addEventListener('DOMContentLoaded', function () {
    fetch('/notifications/unread_count')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.badge.bg-danger');
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error fetching unread notifications:', error));
});
