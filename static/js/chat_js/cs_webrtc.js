const peerConnection = new RTCPeerConnection();

// Capture Video & Audio
navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then(stream => {
        document.getElementById("localVideo").srcObject = stream;
        stream.getTracks().forEach(track => peerConnection.addTrack(track, stream));
    });

// Offer to Call
async function callUser(receiverId) {
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

// ICE Candidate Exchange
peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
        socket.emit("ice_candidate", { candidate: event.candidate, receiver_id: receiverId });
    }
};

socket.on("receive_ice_candidate", (data) => {
    peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
});
