async function getChatUsers() {
    try {
        const response = await fetch("/chat/get_chat_users");
        if (!response.ok) throw new Error("Failed to fetch chat users");

        const users = await response.json();
        if (!Array.isArray(users)) throw new Error("Invalid response format");

        const chatList = document.getElementById("chat-list");
        chatList.innerHTML = "";

        users.forEach(user => {
            const userItem = document.createElement("li");
            userItem.innerHTML = `${user.name} (${user.role})`;
            userItem.dataset.id = user.id;  // Example: "Admin-4"

            if (typeof openChat === "function") {
                userItem.onclick = () => openChat(user.id, user.name);
            } else {
                console.warn("openChat function is not defined.");
            }

            chatList.appendChild(userItem);
        });
    } catch (error) {
        console.error("Error fetching chat users:", error.message);
    }
}
