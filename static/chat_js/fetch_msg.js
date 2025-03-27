
// Javascript for fetch personal messages
    function openPersonalChat(receiverId, receiverName, receiverRole, receiverContact) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");
    let chatFooter = document.querySelector(".chat-footer");
    let newMessageButton = document.getElementById("newMessagePopup");

    console.log("Opening personal chat with:", receiverName, "Contact:", receiverContact);

    chatWindow.setAttribute("data-user-id", receiverId);
    chatWindow.setAttribute("data-user-role", receiverRole);
    chatWindow.setAttribute("data-user-contact", receiverContact);

    chatTitle.textContent = `${receiverName} (${receiverContact})`;
    chatFooter.style.display = "flex";

    chatBody.innerHTML = "<p class='text-muted text-center'>Loading chat...</p>";
    let lastMessageCount = 0;

    if (window.refreshInterval) {
        clearInterval(window.refreshInterval);
    }

    function fetchPersonalMessages() {
        fetch(`/chat/fetch_personal_messages?id=${receiverId}&role=${receiverRole}`)
            .then(response => response.json())
            .then(data => {
                let currentMessageCount = data.messages.length;
                let isScrolledToBottom = chatBody.scrollHeight - chatBody.scrollTop <= chatBody.clientHeight + 5;
                
                chatBody.innerHTML = "";
                if (!data.messages || data.messages.length === 0) {
                    chatBody.innerHTML = "<p class='text-muted text-center'>No messages yet.</p>";
                } else {
                    let senderContact = chatWindow.getAttribute("data-user-contact");
                    let lastDate = "";

                    data.messages.forEach(msg => {
                        let isSender = msg.sender_contact === senderContact;
                        
                        // Manually parse the timestamp: "27-03-2025 04:35:50 PM"
                        let [datePart, timePart, ampm] = msg.timestamp.split(" ");
                        let [day, month, year] = datePart.split("-"); // Split DD-MM-YYYY
                        let formattedDate = `${day}-${month}-${year}`;
                        let formattedTime = `${timePart} ${ampm}`; // Keep time as is

                        // Insert date separator if date changes
                        if (formattedDate !== lastDate) {
                            let dateElement = document.createElement("div");
                            dateElement.classList.add("date-separator");
                            dateElement.textContent = formattedDate;
                            chatBody.appendChild(dateElement);
                            lastDate = formattedDate;
                        }

                        let messageWrapper = document.createElement("div");
                        messageWrapper.classList.add("message-wrapper", isSender ? "sent" : "received");

                        let messageElement = document.createElement("div");
                        messageElement.classList.add("chat-message");

                        messageElement.innerHTML = `
                            <div class="message-text">${msg.text}</div>
                            <div class="text-muted message-time">${formattedTime}</div>
                        `;

                        messageWrapper.appendChild(messageElement);
                        chatBody.appendChild(messageWrapper);
                    });

                    // Scroll to bottom only if opening chat or user is already at the bottom
                    if (currentMessageCount !== lastMessageCount || lastMessageCount === 0 || isScrolledToBottom) {
                        chatBody.scrollTop = chatBody.scrollHeight;
                    }
                }

                if (currentMessageCount > lastMessageCount && !isScrolledToBottom) {
                    newMessageButton.style.display = "block";
                }
                lastMessageCount = currentMessageCount;
            })
            .catch(error => console.error("Error fetching personal messages:", error));
    }

    fetchPersonalMessages();
    window.refreshInterval = setInterval(fetchPersonalMessages, 1000);

    // Force scroll to bottom when opening chat
    setTimeout(() => {
        chatBody.scrollTop = chatBody.scrollHeight;
    }, 200);

    newMessageButton.addEventListener("click", function() {
        chatBody.scrollTop = chatBody.scrollHeight;
        newMessageButton.style.display = "none";
    });
}


// Javascript for fetch group messages
function openGroupChat(groupId, groupName) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");
    let chatFooter = document.querySelector(".chat-footer");
    let newMessageButton = document.getElementById("newMessagePopup");

    console.log("Opening group chat:", groupName);

    chatWindow.setAttribute("data-group-id", groupId);
    chatTitle.textContent = `${groupName} (${groupId})`;
    chatFooter.style.display = "flex";
    chatBody.innerHTML = "<p class='text-muted text-center'>Loading chat...</p>";
    let lastMessageCount = 0;

    if (window.refreshInterval) {
        clearInterval(window.refreshInterval);
    }

    function fetchGroupMessages() {
        fetch(`/chat/fetch_group_messages?group_id=${groupId}`)
            .then(response => response.json())
            .then(data => {
                let currentMessageCount = data.messages.length;
                let isScrolledToBottom = chatBody.scrollTop + chatBody.clientHeight >= chatBody.scrollHeight - 10;

                chatBody.innerHTML = "";
                if (!data.messages || data.messages.length === 0) {
                    chatBody.innerHTML = "<p class='text-muted text-center'>No messages yet.</p>";
                } else {
                    if (data.sender_contact) {
                        localStorage.setItem("sender_contact", data.sender_contact);
                    }

                    let senderContact = localStorage.getItem("sender_contact");
                    console.log("Logged-in user contact:", senderContact);

                    let lastDate = ""; // Track the last displayed date

                    data.messages.forEach(msg => {
                        let isSender = msg.sender_contact === senderContact;
                        let messageWrapper = document.createElement("div");
                        messageWrapper.classList.add("message-wrapper", isSender ? "received" : "sent");

                        let messageElement = document.createElement("div");
                        messageElement.classList.add("chat-message");

                        // Extract date and time from timestamp
                        let [date, time] = msg.timestamp.split(" "); // "27-03-2025 03:51:19 PM"
                        let formattedTime = time; // Keep time as is

                        // Display date only if it's different from the last displayed one
                        if (date !== lastDate) {
                            let dateElement = document.createElement("div");
                            dateElement.classList.add("date-separator");
                            dateElement.innerHTML = `<span>${date}</span>`;
                            chatBody.appendChild(dateElement);
                            lastDate = date; // Update last displayed date
                        }

                        messageElement.innerHTML = `
                            <div class="message-text">${msg.text}</div>
                            <div class="text-muted message-time">${formattedTime}</div>
                        `;

                        messageWrapper.appendChild(messageElement);
                        chatBody.appendChild(messageWrapper);
                    });

                    if (isScrolledToBottom) {
                        chatBody.scrollTop = chatBody.scrollHeight;
                    }
                }

                if (currentMessageCount > lastMessageCount && !isScrolledToBottom) {
                    newMessageButton.style.display = "block";
                } else {
                    newMessageButton.style.display = "none";
                }

                lastMessageCount = currentMessageCount;
            })
            .catch(error => console.error("Error fetching group messages:", error));
    }

    fetchGroupMessages();
    window.refreshInterval = setInterval(fetchGroupMessages, 1000);

    newMessageButton.addEventListener("click", function() {
        chatBody.scrollTop = chatBody.scrollHeight;
        newMessageButton.style.display = "none";
    });

    setTimeout(() => {
        chatBody.scrollTop = chatBody.scrollHeight;
    }, 100);
}
