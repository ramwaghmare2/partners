function sendGlobalMessage(sender_id, message) {
    socket.emit('global_message', { sender_id, message });
}

// Listen for global chat messages
socket.on("global_chat", (data) => {
    console.log("New global message:", data.message);
});
