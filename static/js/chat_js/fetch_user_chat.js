async function getChatUsers() {
    try {
        const response = await fetch("/chat/get_chat_users");
        if (!response.ok) throw new Error("Failed to fetch chat users");

        const data = await response.json();
        if (!Array.isArray(data.users)) throw new Error("Invalid response format");

        const chatList = document.getElementById("chat-list");
        chatList.innerHTML = ""; 

        data.users.forEach(user => {
            const userItem = document.createElement("li");
            userItem.innerHTML = `${user.name} (${user.role})`;
            userItem.dataset.id = user.id;

            userItem.onclick = () => {
                sessionStorage.setItem("receiver_id", user.id); // ✅ Store receiver_id
                console.log(`✅ Selected receiver: ${user.id}`);
                openChat(user.id, user.name);
            };

            chatList.appendChild(userItem);
        });
    } catch (error) {
        console.error("❌ Error fetching chat users:", error.message);
    }
}



async function searchChatUsers(query) {
    try {
        const response = await fetch(`/chat/search_chat_users?query=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error("Failed to fetch search results");

        const data = await response.json();
        if (!Array.isArray(data.users)) throw new Error("Invalid response format");

        const chatList = document.getElementById("chat-list");
        chatList.innerHTML = ""; // Clear existing list

        data.users.forEach(user => {
            const userItem = document.createElement("li");
            userItem.innerHTML = `${user.name} (${user.role})`;
            userItem.dataset.id = user.id;

            userItem.onclick = () => openChat(user.id, user.name);

            chatList.appendChild(userItem);
        });
    } catch (error) {
        console.error("Error fetching chat search results:", error.message);
    }
}

async function loadChatHistory(senderId, receiverId) {
    if (!senderId || !receiverId) {
        console.error("❌ Missing senderId or receiverId:", { senderId, receiverId });
        return;
    }

    try {
        const response = await fetch(`/chat/get_messages?sender_id=${senderId}&receiver_id=${receiverId}`);
        if (!response.ok) throw new Error("Failed to fetch chat history");

        const chatData = await response.json();
        console.log("✅ Chat history loaded:", chatData);
        
        const messageList = document.getElementById("messages");
        messageList.innerHTML = ""; 

        chatData.messages.forEach(msg => {
            const newMessage = document.createElement("li");
            newMessage.textContent = `${new Date(msg.timestamp).toLocaleString()} - ${msg.message}`;
            messageList.appendChild(newMessage);
        });
    } catch (error) {
        console.error("❌ Error fetching chat history:", error.message);
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const senderId = sessionStorage.getItem("user_id");
    const receiverId = sessionStorage.getItem("receiver_id");

    console.log("✅ Checking stored session data:", { senderId, receiverId });

    if (senderId && receiverId) {
        loadChatHistory(senderId, receiverId);
    } else {
        console.warn("⚠️ Missing senderId or receiverId in session storage.");
    }
});
