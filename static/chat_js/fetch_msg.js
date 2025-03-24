function openPersonalChat(receiverId, receiverName, receiverRole) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");
    let chatFooter = document.querySelector(".chat-footer");

    console.log("Opening personal chat with:", receiverName);

    chatWindow.setAttribute("data-user-id", receiverId);
    chatWindow.setAttribute("data-user-role", receiverRole);
    chatTitle.textContent = receiverName;
    chatFooter.style.display = "flex";

    chatBody.innerHTML = "<p class='text-muted text-center'>Loading chat...</p>";

    if (window.refreshInterval) {
        clearInterval(window.refreshInterval);
    }

    function fetchPersonalMessages() {
        fetch(`/chat/fetch_personal_messages?id=${receiverId}&role=${receiverRole}`)
            .then(response => response.json())
            .then(data => {
                chatBody.innerHTML = "";
                if (!data.messages || data.messages.length === 0) {
                    chatBody.innerHTML = "<p class='text-muted text-center'>No messages yet.</p>";
                } else {
                    data.messages.forEach(msg => {
                        let messageElement = document.createElement("div");
                        messageElement.classList.add("chat-message");
                        messageElement.innerHTML = `
                            <div class="message-user">${msg.sender_name}</div>
                            <div class="message-text">${msg.text}</div>
                            <div class="text-muted message-time" style="font-size: 0.8em;">${msg.timestamp}</div>
                        `;
                        chatBody.appendChild(messageElement);
                    });
                    chatBody.scrollTop = chatBody.scrollHeight;
                }
            })
            .catch(error => console.error("Error fetching personal messages:", error));
    }

    fetchPersonalMessages();
    window.refreshInterval = setInterval(fetchPersonalMessages, 1000);
}




function openGroupChat(groupId, groupName) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");
    let chatFooter = document.querySelector(".chat-footer");

    console.log("Opening group chat:", groupName);

    chatWindow.setAttribute("data-group-id", groupId);
    chatTitle.textContent = groupName;
    chatFooter.style.display = "flex";

    chatBody.innerHTML = "<p class='text-muted text-center'>Loading chat...</p>";

    if (window.refreshInterval) {
        clearInterval(window.refreshInterval);
    }

    function fetchGroupMessages() {
        fetch(`/chat/fetch_group_messages?group_id=${groupId}`)
            .then(response => response.json())
            .then(data => {
                chatBody.innerHTML = "";
                if (!data.messages || data.messages.length === 0) {
                    chatBody.innerHTML = "<p class='text-muted text-center'>No messages yet.</p>";
                } else {
                    data.messages.forEach(msg => {
                        let messageElement = document.createElement("div");
                        messageElement.classList.add("chat-message");
                        messageElement.innerHTML = `
                            <div class="message-user">${msg.sender_name}</div>
                            <div class="message-text">${msg.text}</div>
                            <div class="text-muted message-time" style="font-size: 0.8em;">${msg.timestamp}</div>
                        `;
                        chatBody.appendChild(messageElement);
                    });
                    chatBody.scrollTop = chatBody.scrollHeight;
                }
            })
            .catch(error => console.error("Error fetching group messages:", error));
    }

    fetchGroupMessages();
    window.refreshInterval = setInterval(fetchGroupMessages, 1000);
}
