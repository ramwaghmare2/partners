document.addEventListener("DOMContentLoaded", () => {
    const signupForm = document.getElementById("signupForm");
    const loginForm = document.getElementById("loginForm");

    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(signupForm);
            const data = {
                name: formData.get("name"),
                email: formData.get("email"),
                role: formData.get("role"),
                contact: formData.get("contact"),
                password: formData.get("password"),
                confirmPassword: formData.get("confirmPassword")
            };
            const response = await fetch("/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            alert(result.message || result.error);
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const data = {
                email: formData.get("email"),
                password: formData.get("password"),
                role: formData.get("role"),
            };
            const response = await fetch("/admin/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            alert(result.message || result.error);
            if (response.ok) {
                window.location.href = "/admin";
            }
        });
    }
});


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