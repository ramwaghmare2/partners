import { io } from "socket.io-client";

// ✅ Set backend URL properly (for Vite or fallback)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || window.location.origin;
const socket = io(BACKEND_URL, { transports: ["websocket"] }); // Ensure WebSocket is prioritized

// ✅ Join Chat Room (For Private or Group Chat)
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

    socket.on("room_joined", (data) => {
        console.log(`✅ Joined room: ${data.room}`);
    });
}

// ✅ Leave Chat Room
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

    socket.on("room_left", (data) => {
        console.log(`🚪 Left room: ${data.room}`);
    });
}

// ✅ Listen for Private Messages
socket.on("receive_message", (data) => {
    console.log(`📩 New message from ${data.sender_id}: ${data.message}`);
    displayMessage(data);
});

// ✅ Listen for Group Messages
socket.on("receive_group_message", (data) => {
    console.log(`👥 New group message in ${data.group_id}: ${data.message}`);
    displayMessage(data);
});

// ✅ Display Messages in UI
function displayMessage(data) {
    const messageList = document.getElementById("messages");
    const newMessage = document.createElement("li");
    newMessage.textContent = `${data.sender_id}: ${data.message}`;
    messageList.appendChild(newMessage);
}

// ✅ Handle Connection Errors & Reconnect
socket.on("connect_error", (error) => {
    console.error("❌ WebSocket connection failed:", error.message);
});

socket.on("disconnect", (reason) => {
    console.warn(`⚠️ Disconnected from server (${reason}). Reconnecting...`);
    setTimeout(() => {
        socket.connect(); // Auto-reconnect
    }, 3000);
});

// ✅ Export Functions
export { socket, joinChat, leaveChat };
