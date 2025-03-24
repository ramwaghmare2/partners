
let socket = io("http://localhost:5000"); // Connect to Socket.IO server

function openChat(receiverId, receiverName, receiverRole) {
    let chatWindow = document.getElementById("chatWindow");
    let chatTitle = document.getElementById("chatTitle");
    let chatBody = document.getElementById("chatBody");

    console.log("Opening chat with:", receiverId, receiverName, receiverRole);

    // Set receiver details in the chat window
    chatWindow.setAttribute("data-user-id", receiverId);
    chatWindow.setAttribute("data-user-role", receiverRole);
    chatTitle.textContent = receiverName; // Set chat title

    // Clear chat messages when switching
    chatBody.innerHTML = "<p class='text-muted text-center'>Loading chat...</p>";

    // Emit a request to fetch messages via Socket.IO
    socket.emit("fetch_messages", { id: receiverId, role: receiverRole });

    // Listen for the messages response
    socket.on("fetch_messages_response", (data) => {
        console.log("Received messages:", data); // Debugging output

        chatBody.innerHTML = ""; // Clear loading text

        if (!data.messages || data.messages.length === 0) {
            chatBody.innerHTML = "<p class='text-muted text-center'>No messages yet.</p>";
        } else {
            data.messages.forEach((msg) => {
                let messageElement = document.createElement("p");
                messageElement.innerHTML = `${msg.text} 
                    <span class="text-muted" style="font-size: 0.8em;">${msg.timestamp}</span>`;
                chatBody.appendChild(messageElement);
            });
        }
    });

    // Listen for errors
    socket.on("fetch_error", (error) => {
        console.error("Error fetching messages:", error);
        chatBody.innerHTML = `<p class='text-danger text-center'>${error.error}</p>`;
    });

    // Join a specific chat room based on receiver ID
    socket.emit("join_room", { id: receiverId, role: receiverRole });
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


