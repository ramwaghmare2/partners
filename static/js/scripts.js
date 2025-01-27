/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});


document.addEventListener('DOMContentLoaded', function () {
    const rowsPerPage = 10;  // Number of rows per page
    const rows = document.querySelectorAll('#OrderTable tbody tr');  // All rows in the table body
    const totalRows = rows.length;  // Total number of rows
    const totalPages = Math.ceil(totalRows / rowsPerPage);  // Total pages
    const paginationControls = document.getElementById('pagination-controls');  // Pagination controls div

    let currentPage = 1;  // Current page is initially 1

    // Function to paginate the table
    function paginate() {
        // Hide all rows initially
        rows.forEach(row => row.style.display = 'none');

        // Calculate the start and end indexes for the current page
        const startIdx = (currentPage - 1) * rowsPerPage;
        const endIdx = startIdx + rowsPerPage;

        // Show only the rows for the current page
        for (let i = startIdx; i < endIdx && i < rows.length; i++) {
            rows[i].style.display = '';  // Display the row
        }

        // Update pagination controls
        paginationControls.innerHTML = '';  // Clear existing controls

        // Create Previous Button
        const prevButton = document.createElement('button');
        prevButton.textContent = '<';
        prevButton.classList.add('arrow');
        if (currentPage === 1) prevButton.classList.add('disabled');  // Disable if on first page
        prevButton.onclick = function () {
            if (currentPage > 1) {
                currentPage--;  // Go to previous page
                paginate();
            }
        };
        paginationControls.appendChild(prevButton);

        // Display Current Page Number
        const pageDisplay = document.createElement('span');
        pageDisplay.textContent = `Page ${currentPage} of ${totalPages}`;
        pageDisplay.classList.add('page-display');
        paginationControls.appendChild(pageDisplay);

        // Create Next Button
        const nextButton = document.createElement('button');
        nextButton.textContent = '>';
        nextButton.classList.add('arrow');
        if (currentPage === totalPages) nextButton.classList.add('disabled');  // Disable if on last page
        nextButton.onclick = function () {
            if (currentPage < totalPages) {
                currentPage++;  // Go to next page
                paginate();
            }
        };
        paginationControls.appendChild(nextButton);
    }

    // Initialize pagination when the page is loaded
    paginate();
});



// Password Toggle Script
function togglePassword() {
    var passwordField = document.getElementById("password");
    var eyeIcon = document.getElementById("eye-icon");
    
    // Toggle the type attribute between password and text
    if (passwordField.type === "password") {
        passwordField.type = "text";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
    } else {
        passwordField.type = "password";
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    }
}

function toggleRePassword() {
    var rePasswordField = document.getElementById("re_password");
    var reEyeIcon = document.getElementById("re-eye-icon");
    
    // Toggle the type attribute between password and text
    if (rePasswordField.type === "password") {
        rePasswordField.type = "text";
        reEyeIcon.classList.remove("fa-eye");
        reEyeIcon.classList.add("fa-eye-slash");
    } else {
        rePasswordField.type = "password";
        reEyeIcon.classList.remove("fa-eye-slash");
        reEyeIcon.classList.add("fa-eye");
    }
}

// Example: Toggle notifications
const bellLink = document.querySelector('.nav-link');

// Simulate notifications
const hasNotifications = true;

if (hasNotifications) {
    bellLink.classList.add('has-notifications');
} else {
    bellLink.classList.remove('has-notifications');
}
