function sendGroupMessage(sender_id, group_id, message) {
    socket.emit('group_message', { sender_id, group_id, message });
}

// Listen for group messages
socket.on(`group_message_${USER_ID}`, (data) => {
    console.log("New group message:", data.message);
});
