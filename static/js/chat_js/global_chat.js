// Import sendGlobalMessage from client_side.js
import { sendGlobalMessage } from "./client_side.js";

// Listen for global chat messages (Handled in client_side.js)
console.log("Global chat module loaded.");

function sendGlobalMessage() {
    // Your existing send logic
    const messageContainer = document.getElementById("global-messages");
    messageContainer.scrollTop = messageContainer.scrollHeight; // Auto-scroll
}
