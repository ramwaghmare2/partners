const peerConnection = new RTCPeerConnection();
let localStream = null;

// Capture Video & Audio with Error Handling
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

// Offer to Call
async function callUser(receiverId) {
    if (!receiverId) {
        console.error("Receiver ID is required to make a call.");
        return;
    }
    
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    
    socket.emit("offer", { offer, receiver_id: receiverId });
}

// Handle Incoming Offer
socket.on("receive_offer", async (data) => {
    await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    
    socket.emit("answer", { answer, sender_id: data.sender_id });
});

// Handle Answer
socket.on("receive_answer", async (data) => {
    await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
});

// ICE Candidate Exchange with Receiver ID Fix & Empty Candidate Check
peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
        const receiverId = getCurrentReceiverId(); // Ensure we have a receiverId
        if (receiverId) {
            socket.emit("ice_candidate", { candidate: event.candidate, receiver_id: receiverId });
        } else {
            console.warn("ICE candidate event triggered without a valid receiverId.");
        }
    }
};

socket.on("receive_ice_candidate", (data) => {
    if (data.candidate) {
        peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate)).catch(error => {
            console.error("Error adding received ICE candidate:", error);
        });
    }
});

// Function to Retrieve Current Receiver ID (Placeholder)
function getCurrentReceiverId() {
    // Implement logic to store and retrieve the correct receiverId
    return window.currentReceiverId || null;
}