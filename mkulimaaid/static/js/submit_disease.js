function showLoadingAnimation() {
    // Hide upload button and preview image
    document.querySelector(".upload-section form").style.display = "none";

    // Show loading animation
    document.getElementById("loading-animation").classList.remove("d-none");
}

// Ensure the page resets correctly when it loads (if necessary)
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("loading-animation").classList.add("d-none");
});
