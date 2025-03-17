// Import sendGroupMessage from client_side.js
import { sendGroupMessage } from "./client_side.js";

// Get the current user ID dynamically (assuming it's stored in sessionStorage)
const userId = sessionStorage.getItem("user_id") || localStorage.getItem("user_id");

if (userId) {
    // Listen for group messages dynamically
    socket.on(`group_message_${userId}`, (data) => {
        console.log("New group message:", data.message);
    });
} else {
    console.error("User ID not found. Group chat listener not initialized.");
}
