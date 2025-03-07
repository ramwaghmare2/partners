async function getChatUsers() {
    const response = await fetch("/get_chat_users");
    const users = await response.json();

    const chatList = document.getElementById("chat-list");
    chatList.innerHTML = "";

    users.forEach(user => {
        const userItem = document.createElement("li");
        userItem.innerHTML = `${user.name} (${user.role})`;
        userItem.dataset.id = user.id;  // Example: "Admin-4"
        userItem.onclick = () => openChat(user.id, user.name);
        chatList.appendChild(userItem);
    });
}
