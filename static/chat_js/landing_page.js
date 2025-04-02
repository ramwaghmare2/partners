let refreshInterval;

function openChat(receiverId, receiverName, receiverRole = null, groupPhoto = null) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");
    let chatFooter = document.querySelector(".chat-footer");
    let chatHeader = document.querySelector(".chat-header");  // The container for chat title and image

    // Debugging logs
    console.log('Receiver ID:', receiverId);
    console.log('Receiver Name:', receiverName);
    console.log('Receiver Role:', receiverRole || 'Group Chat');

    // Set receiver details in the chat window
    chatWindow.setAttribute("data-user-id", receiverId);
    chatWindow.setAttribute("data-user-role", receiverRole || "group");
    chatTitle.textContent = receiverName;  // Set the chat title

    // If it's a group chat, show group photo in a circle
    if (groupPhoto) {
        // Set image URL for group photo, defaulting to a placeholder image if not available
        let groupImageElement = chatHeader.querySelector(".group-image");
        groupImageElement.src = groupPhoto || "path/to/default/group-image.png"; // Set the image source
        groupImageElement.style.display = "block";  // Ensure the image is visible
    }

    // Show chat input area
    chatFooter.style.display = "flex";

    // Clear previous chat messages
    chatBody.innerHTML = "<p class='text-muted text-center'>Loading chat...</p>";

    // Clear any existing interval before starting a new one
    if (window.refreshInterval) {
        clearInterval(window.refreshInterval);
    }

    // Function to fetch messages
    function fetchMessages() {
        let fetchUrl = receiverRole 
            ? `/chat/fetch_messages?id=${receiverId}&role=${receiverRole}`  // Individual chat
            : `/chat/fetch_group_messages?group_id=${receiverId}`;  // Group chat

        fetch(fetchUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then(data => {
                console.log("Fetched Messages:", data); // Debugging output
                chatBody.innerHTML = "";  // Clear loading text

                if (!data.messages || data.messages.length === 0) {
                    chatBody.innerHTML = "<p class='text-muted text-center'>No messages yet.</p>";
                } else {
                    data.messages.forEach(msg => {
                        let messageElement = document.createElement("div");
                        messageElement.classList.add("chat-message");

                        // Format the message
                        messageElement.innerHTML = `
                            <div class="message-user">${msg.sender_name}</div>
                            <div class="message-text">${msg.text}</div>
                            <div class="text-muted message-time" style="font-size: 0.8em;">${msg.timestamp}</div>
                        `;

                        chatBody.appendChild(messageElement);
                    });

                    // Auto-scroll to the latest message
                    chatBody.scrollTop = chatBody.scrollHeight;
                }
            })
            .catch(error => console.error("Error fetching messages:", error));
    }

    // Fetch messages initially and refresh every second
    fetchMessages();
    window.refreshInterval = setInterval(fetchMessages, 1000);
}



       document.addEventListener("DOMContentLoaded", function () {
    let searchInput = document.getElementById("searchUser");
    let resultsDiv = document.getElementById("searchResults");
    let chatList = document.getElementById('personalChats');

    // Handle Search Input
    searchInput.addEventListener('input', function () {
        let query = this.value.trim();

        if (query.length === 0) {
            hideSearchResults();
            return;
        }

        fetch(`/chat/search_users?q=${query}`)
            .then(response => response.json())
            .then(data => {
                resultsDiv.innerHTML = "";
                resultsDiv.style.display = "block"; // Show dropdown

                data.forEach(user => {
                    let item = document.createElement('a');
                    item.href = "#";
                    item.classList.add("list-group-item", "list-group-item-action", "search-result-item");
                    item.innerHTML = `<strong>${user.name}</strong> <span class="text-muted">(${user.role})</span>`;
                    item.dataset.userId = user.user_id;
                    item.dataset.userName = user.name;
                    item.dataset.userRole = user.role;

                    // Handle click selection
                    item.addEventListener("click", function () {
                        startPersonalChat(user.user_id, user.name, user.role);
                        hideSearchResults();
                    });

                    resultsDiv.appendChild(item);
                });
            })
            .catch(error => console.error("Error searching users:", error));
    });

    // Handle keyboard navigation
    searchInput.addEventListener("keydown", function (event) {
        let activeItem = document.querySelector(".search-result-item.active");
        let items = [...resultsDiv.getElementsByClassName("search-result-item")];

        if (event.key === "ArrowDown") {
            event.preventDefault();
            if (activeItem) {
                let next = activeItem.nextElementSibling;
                if (next) {
                    activeItem.classList.remove("active");
                    next.classList.add("active");
                }
            } else if (items.length > 0) {
                items[0].classList.add("active");
            }
        } 
        else if (event.key === "ArrowUp") {
            event.preventDefault();
            if (activeItem) {
                let prev = activeItem.previousElementSibling;
                if (prev) {
                    activeItem.classList.remove("active");
                    prev.classList.add("active");
                }
            }
        } 
        else if (event.key === "Enter") {
            event.preventDefault();
            if (activeItem) {
                activeItem.click();  // Trigger click event for selected item
            }
        }
    });

    //Hide search results when clicking outside
    document.addEventListener("click", function (event) {
        if (!searchInput.contains(event.target) && !resultsDiv.contains(event.target)) {
            hideSearchResults();
        }
    });

    function startPersonalChat(receiverId, receiverName, receiverRole) {
        fetch('/chat/start_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver_id: receiverId, name: receiverName, role: receiverRole })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
                return;
            }

            let exists = [...chatList.children].some(li => li.dataset.userId === receiverId);

            if (!exists) {
                let newChat = document.createElement('li');
                newChat.classList.add("list-group-item", "bg-transparent", "text-white");
                newChat.innerHTML = `${receiverName} <span class="text-muted">(${receiverRole})</span>`;
                newChat.dataset.userId = receiverId;
                newChat.dataset.userRole = receiverRole;
                newChat.onclick = function () {
                    openChat(receiverId, receiverName);
                };
                chatList.appendChild(newChat);
            }

            openChat(receiverId, receiverName);
            hideSearchResults();
        })
        .catch(error => console.error("Error starting chat:", error));
    }


    function hideSearchResults() {
        resultsDiv.innerHTML = "";
        resultsDiv.style.display = "none";
        searchInput.value = "";
    }
});


