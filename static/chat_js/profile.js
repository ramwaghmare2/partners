
// Veiw user profile of in chat list
    function viewUserProfile(event, userId, userName, userEmail, userRole, userContact) {
        event.stopPropagation(); // Prevent chat opening

        // Set profile details
        document.getElementById('profileName').innerText = userName;
        document.getElementById('profileEmail').innerText = userEmail || 'N/A';
        document.getElementById('profileRole').innerText = userRole;
        document.getElementById('profileContact').innerText = userContact || 'N/A';

        // Show the modal
        var profileModal = new bootstrap.Modal(document.getElementById('userProfileModal'));
        profileModal.show();
    }
 
// JavaScript for Sidebar Toggle 

function toggleUserSidebar() {
    let sidebar = document.getElementById("userSidebar");

    if (sidebar.style.transform === "translateX(0%)") {
        sidebar.style.transform = "translateX(100%)";
        document.removeEventListener("click", closeSidebarOnOutsideClick);
    } else {
        sidebar.style.transform = "translateX(0%)";
        setTimeout(() => {
            document.addEventListener("click", closeSidebarOnOutsideClick);
        }, 100); // Delay to prevent immediate closing when opening
    }
}

function closeSidebarOnOutsideClick(event) {
    let sidebar = document.getElementById("userSidebar");
    if (!sidebar.contains(event.target)) {
        sidebar.style.transform = "translateX(100%)";
        document.removeEventListener("click", closeSidebarOnOutsideClick);
    }
}


