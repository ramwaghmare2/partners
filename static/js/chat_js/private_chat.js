const socket = io('http://localhost:5000');

function sendPrivateMessage(sender_id, receiver_id, message) {
    socket.emit('private_message', { sender_id, receiver_id, message });
}

socket.on(`private_message_${USER_ID}`, (data) => {
    console.log("New private message:", data.message);
});
