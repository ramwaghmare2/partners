const socket = io("http://localhost:5000");

// Send Private Message
function sendPrivateMessage(senderId, receiverId, message) {
    socket.emit("private_message", { sender_id: senderId, receiver_id: receiverId, message: message });
}

// Send Group Message
function sendGroupMessage(senderId, groupId, message) {
    socket.emit("group_message", { sender_id: senderId, group_id: groupId, message: message });
}

// Send Global Message
function sendGlobalMessage(senderId, message) {
    socket.emit("global_message", { sender_id: senderId, message: message });
}

// Listen for Messages
socket.on("receive_message", (data) => {
    console.log(`New Message: ${data.message} (Type: ${data.chat_type})`);
});





// Listen for Message Status Updates
socket.on("message_status_update", (data) => {
    console.log(`Message ID ${data.message_id} is now ${data.status}`);
});

// Mark Message as Delivered
function markMessageAsDelivered(messageId) {
    socket.emit("message_delivered", { message_id: messageId });
}

// Mark Message as Seen
function markMessageAsSeen(messageId) {
    socket.emit("message_seen", { message_id: messageId });
}



// Upload File
async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/upload", {
        method: "POST",
        body: formData,
    });

    const data = await response.json();
    if (data.file_url) {
        return data.file_url;
    } else {
        console.error("File upload failed:", data.error);
    }
}

// Send File Message
async function sendFileMessage(senderId, receiverId, file) {
    const fileUrl = await uploadFile(file);
    if (fileUrl) {
        socket.emit("file_message", {
            sender_id: senderId,
            receiver_id: receiverId,
            file_url: fileUrl,
            file_type: file.type
        });
    }
}

// Listen for Incoming Files
socket.on("receive_file", (data) => {
    console.log(`New File Received: ${data.file_url} (Type: ${data.file_type})`);
});



// Load more messages
let currentPage = 1;
let loading = false;

async function loadMessages() {
    if (loading) return;
    loading = true;

    const response = await fetch(`/get_messages?sender_id=${senderId}&receiver_id=${receiverId}&page=${currentPage}`);
    const messages = await response.json();

    if (messages.length > 0) {
        currentPage++;
        messages.forEach(displayMessage); // Function to add messages to UI
    }

    loading = false;
}

// Detect scroll up to load older messages
document.getElementById("chat-box").addEventListener("scroll", function () {
    if (this.scrollTop === 0) {
        loadMessages();
    }
});
