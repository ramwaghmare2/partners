const socket = io("http://localhost:5000");

const peerConnection = new RTCPeerConnection();
let localStream = null;
let currentReceiverId = null; // Store the receiver ID

// Function to Start Media (Camera & Mic)
async function startMedia() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        document.getElementById("localVideo").srcObject = localStream;
        localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
    } catch (error) {
        console.error("Error accessing media devices:", error);
        alert("Failed to access camera/microphone. Please check your permissions.");
    }
}

startMedia();

// 📩 Send a Chat Message
const USER_ID = sessionStorage.getItem("user_id");
const RECEIVER_ID = sessionStorage.getItem("receiver_id");

function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const message = messageInput.value.trim();
    
    if (message && USER_ID && RECEIVER_ID) {
        socket.emit("private_message", { sender_id: USER_ID, receiver_id: RECEIVER_ID, message: message });
        messageInput.value = "";
    }
}


// 📥 Receive Chat Message
socket.on("receive_message", (data) => {
    const messageList = document.getElementById("messages");
    const newMessage = document.createElement("li");
    newMessage.textContent = `${data.sender_id}: ${data.message}`;
    messageList.appendChild(newMessage);
});

// 📞 Offer to Call (Start Video Call)
async function callUser(receiverId) {
    if (!receiverId) {
        console.error("Receiver ID is required to make a call.");
        return;
    }
    
    currentReceiverId = receiverId; // Store the receiver ID
    
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    
    socket.emit("offer", { offer, receiver_id: receiverId, sender_id: USER_ID });
}

// 📥 Handle Incoming Offer
socket.on("receive_offer", async (data) => {
    currentReceiverId = data.sender_id; // Store sender as receiver
    
    await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    
    socket.emit("answer", { answer, sender_id: USER_ID, receiver_id: data.sender_id });
});

// 📥 Handle Answer
socket.on("receive_answer", async (data) => {
    await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
});

// 🔄 ICE Candidate Exchange
peerConnection.onicecandidate = (event) => {
    if (event.candidate && currentReceiverId) {
        socket.emit("ice_candidate", { candidate: event.candidate, receiver_id: currentReceiverId });
    }
};

socket.on("receive_ice_candidate", (data) => {
    if (data.candidate) {
        peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate)).catch(error => {
            console.error("Error adding received ICE candidate:", error);
        });
    }
});

// 🔍 Function to Set Current Receiver ID
function setCurrentReceiverId(receiverId) {
    currentReceiverId = receiverId;
}

function addMessage(sender, message) {
    const messageList = document.getElementById("messages");
    const newMessage = document.createElement("li");
    newMessage.textContent = `${sender}: ${message}`;
    messageList.appendChild(newMessage);

    // ✅ Auto-scroll to the latest message
    messageList.scrollTop = messageList.scrollHeight;
}

// Uploads files
async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/chat/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log("File uploaded:", result.file_url);
    } catch (error) {
        console.error("File upload failed:", error.message);
    }
}
