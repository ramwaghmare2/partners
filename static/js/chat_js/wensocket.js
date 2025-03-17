import { io } from "socket.io-client";

// Use environment variable or fallback to relative path
const BACKEND_URL = process.env.BACKEND_URL || window.location.origin;
const socket = io(BACKEND_URL);

// Import centralized WebSocket handlers from client_side.js
import { sendPrivateMessage, sendGroupMessage, sendGlobalMessage } from "./client_side.js";

// Join Chat Room (For Private or Group Chat)
function joinChat(userId, groupId = null) {
    if (!userId) {
        console.error("User ID is required to join a chat.");
        return;
    }
    const roomData = { user_id: userId };
    if (groupId) {
        roomData.group_id = groupId;
    }
    socket.emit("join_room", roomData);
}

// Leave Chat Room
function leaveChat(userId, groupId = null) {
    if (!userId) {
        console.error("User ID is required to leave a chat.");
        return;
    }
    const roomData = { user_id: userId };
    if (groupId) {
        roomData.group_id = groupId;
    }
    socket.emit("leave_room", roomData);
}

// Export functions
export { socket, joinChat, leaveChat };
