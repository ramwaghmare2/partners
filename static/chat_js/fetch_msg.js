function openPersonalChat(receiverId, receiverName, receiverRole, receiverContact) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");
    let chatFooter = document.querySelector(".chat-footer");

    console.log("Opening personal chat with:", receiverName, "Contact:", receiverContact);

    chatWindow.setAttribute("data-user-id", receiverId);
    chatWindow.setAttribute("data-user-role", receiverRole);
    chatWindow.setAttribute("data-user-contact", receiverContact);  // Store the contact in the chat window

    chatTitle.textContent = `${receiverName} (${receiverContact})`; // Display contact in the chat title
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



function openEditGroupModal() {
    let chatWindow = document.getElementById("chatWindow");
    let groupId = chatWindow.getAttribute("data-group-id");
    let groupName = document.getElementById("chatTitle").textContent;

    if (!groupId) {
        alert("No group selected!");
        return;
    }

    document.getElementById("groupId").value = groupId;
    document.getElementById("groupName").value = groupName;
    
    // Fetch existing group data
    fetch(`/chat/get_group_details?group_id=${groupId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("groupDescription").value = data.description || "";
            document.getElementById("groupParticipants").value = data.participants.join(", ");
        })
        .catch(error => console.error("Error fetching group details:", error));

    let modal = new bootstrap.Modal(document.getElementById("editGroupModal"));
    modal.show();
}

function saveGroupChanges() {
    let groupId = document.getElementById("groupId").value;
    let groupName = document.getElementById("groupName").value;
    let groupDescription = document.getElementById("groupDescription").value;
    let participants = document.getElementById("groupParticipants").value.split(",").map(p => p.trim());

    fetch(`/chat/update_group`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ group_id: groupId, name: groupName, description: groupDescription, participants })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Group updated successfully!");
            document.getElementById("chatTitle").textContent = groupName;
            let modal = bootstrap.Modal.getInstance(document.getElementById("editGroupModal"));
            modal.hide();
        } else {
            alert("Error updating group: " + data.error);
        }
    })
    .catch(error => console.error("Error updating group:", error));
}
