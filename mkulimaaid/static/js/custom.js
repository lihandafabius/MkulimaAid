window.onload = function() {
    var alertMessage = document.getElementById("alert-message");

    // Check if the alert message has content
    if (alertMessage && alertMessage.innerHTML.trim() !== "") {
        alertMessage.style.display = "block"; // Make visible
        alertMessage.classList.add("show");   // Trigger animation

        // Hide the alert after 3 seconds
        setTimeout(function() {
            alertMessage.classList.remove("show");
            setTimeout(function() {
                alertMessage.style.display = "none";
            }, 500); // Allow time for animation to complete
        }, 3000);
    }
};
