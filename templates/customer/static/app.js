// JavaScript for handling customer actions

// Simulate form validation for demonstration
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (event) => {
            const inputs = form.querySelectorAll('input');
            let valid = true;
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    alert(`${input.name} cannot be empty.`);
                }
            });

            if (!valid) {
                event.preventDefault();
            }
        });
    });
});

// Example usage for profile page
function loadProfileData() {
    fetch('/customer/profile', {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        }
    })
        .then(response => response.json())
        .then(data => {
            const profileContainer = document.getElementById('profile');
            if (data.profile) {
                profileContainer.innerHTML = `
                    <p>Name: ${data.profile.name}</p>
                    <p>Email: ${data.profile.email}</p>
                    <p>Contact: ${data.profile.contact}</p>
                    <p>Address: ${data.profile.address}</p>
                    <p>Created At: ${data.profile.created_at}</p>
                `;
            } else {
                profileContainer.innerHTML = '<p>User not found!</p>';
            }
        })
        .catch(err => console.error('Error fetching profile:', err));
}
