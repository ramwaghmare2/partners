// Function to show the user profile
function showUserProfile(user) {
    // Set the dynamic content
    document.getElementById('profileName').innerText = user.name || 'N/A';
    document.getElementById('profileRole').innerText = user.role || 'N/A';
    document.getElementById('profileEmail').innerText = user.email || 'N/A';
    document.getElementById('profileContact').innerText = user.contact || 'N/A';
    
    // Handle the profile picture (fallback if no picture is provided)
    document.getElementById('profilePicture').src = user.profile_picture_url || 'https://via.placeholder.com/100';

    // Show the modal
    var profileModal = new bootstrap.Modal(document.getElementById('userProfileModal'));
    profileModal.show();
}

// Trigger showing the profile modal (this could be triggered by an event in your actual app)
showUserProfile(user);

 
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


