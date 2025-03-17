// Import sendPrivateMessage from client_side.js
import { sendPrivateMessage } from "./client_side.js";

// Get the current user ID dynamically (assuming it's stored in sessionStorage)
const userId = sessionStorage.getItem("user_id") || localStorage.getItem("user_id");

if (userId) {
    // Listen for private messages dynamically
    socket.on(`private_message_${userId}`, (data) => {
        console.log("New private message:", data.message);
    });
} else {
    console.error("User ID not found. Private chat listener not initialized.");
}
