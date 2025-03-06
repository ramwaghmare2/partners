import { io } from "socket.io-client";

const socket = io("http://your-backend-ip:5000");

// Send Private Message
function sendPrivateMessage(senderId, receiverId, message) {
    socket.emit("private_message", { sender_id: senderId, receiver_id: receiverId, message: message });
}

// Receive Private Message
socket.on("private_message", (data) => {
    console.log("Private message received:", data);
});

// Send Group Message
function sendGroupMessage(senderId, groupId, message) {
    socket.emit("group_message", { sender_id: senderId, group_id: groupId, message: message });
}

// Receive Group Message
socket.on("group_message", (data) => {
    console.log("Group message received:", data);
});

// Send Global Message
function sendGlobalMessage(senderId, message) {
    socket.emit("global_message", { sender_id: senderId, message: message });
}

// Receive Global Message
socket.on("global_message", (data) => {
    console.log("Global message received:", data);
});

// Join Chat Room (For Private or Group Chat)
function joinChat(userId, groupId = null) {
    socket.emit("join_room", { user_id: userId, group_id: groupId });
}

// Leave Chat Room
function leaveChat(userId, groupId = null) {
    socket.emit("leave_room", { user_id: userId, group_id: groupId });
}
