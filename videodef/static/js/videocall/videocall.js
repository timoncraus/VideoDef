const roomName = document.getElementById('videos').dataset.roomName;
let ws = new WebSocket(`ws://${window.location.host}/ws/videocall/${roomName}/`);
const configuration = {
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
};
let peerConnection = new RTCPeerConnection(configuration);
document.addEventListener('DOMContentLoaded', () => {
    const localVideo = document.getElementById("localVideo");
    const remoteVideo = document.getElementById("remoteVideo");

    let pendingCandidates = [];


    function setPeerConnectionOntrack() {
        peerConnection.ontrack = event => {
            if (event.streams.length > 0) {
                const remoteStream = event.streams[0];
                if (remoteVideo.srcObject !== remoteStream) {
                    remoteVideo.srcObject = remoteStream;
                }
            }
        };
    }

    setPeerConnectionOntrack();

    function setPeerConnectionOnicecandidate() {
        peerConnection.onicecandidate = event => {
            if (event.candidate) {
                ws.send(JSON.stringify({ type: 'ice', candidate: event.candidate }));
            }
        };
    }
    setPeerConnectionOnicecandidate();



    peerConnection.oniceconnectionstatechange = () => {
        if (peerConnection.iceConnectionState === 'failed') {
            peerConnection.close();
            peerConnection = new RTCPeerConnection(configuration);
            setPeerConnectionOntrack();
            setPeerConnectionOnicecandidate();
        }
    };

    navigator.mediaDevices.enumerateDevices()
        .then(devices => {
            const videoDevice = devices.find(d => d.kind === 'videoinput' && !d.label.toLowerCase().includes('droidcam'));
            if (!videoDevice) throw new Error("Нет подходящей камеры");

            return navigator.mediaDevices.getUserMedia({
                video: { deviceId: videoDevice.deviceId },
                audio: true
            });
        })
        .then(stream => {
            localVideo.srcObject = stream;
            stream.getTracks().forEach(track => peerConnection.addTrack(track, stream));
            updateButtonColors();

            if (isInitiator) {
                peerConnection.createOffer()
                    .then(offer => {
                        return peerConnection.setLocalDescription(offer).then(() => {
                            ws.send(JSON.stringify({ type: 'offer', offer }));
                        });
                    });
            }
        });

    let isInitiator = false;

    ws.onmessage = async(event) => {
        const data = JSON.parse(event.data);
        console.log(data)

        if (data.type === 'end_call') {
            closeVideocall();
        }

        if (data.type === 'ready' && isInitiator) {
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            ws.send(JSON.stringify({ type: 'offer', offer }));
        }

        if (data.type === 'resend_offer' && isInitiator) {
            location.reload();
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            ws.send(JSON.stringify({ type: 'offer', offer }));
        }

        if (data.type === 'role') {
            isInitiator = data.initiator;
        } else if (data.type === 'offer') {
            if (isInitiator) {
                return;
            }
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));

            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);

            ws.send(JSON.stringify({ type: 'answer', answer }));

            pendingCandidates.forEach(c => peerConnection.addIceCandidate(c));
            pendingCandidates = [];

        } else if (data.type === 'answer') {
            if (!isInitiator) {
                return;
            }
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));

            pendingCandidates.forEach(c => peerConnection.addIceCandidate(c));
            pendingCandidates = [];

        } else if (data.type === 'ice') {
            if (peerConnection.remoteDescription) {
                await peerConnection.addIceCandidate(data.candidate);
            } else {
                pendingCandidates.push(data.candidate);
            }
        }
    };
});


function toggleMic() {
    let localStream = document.getElementById("localVideo").srcObject;
    localStream.getAudioTracks().forEach(track => track.enabled = !track.enabled);
    updateButtonColors();
}

function toggleCam() {
    let localStream = document.getElementById("localVideo").srcObject;
    localStream.getVideoTracks().forEach(track => track.enabled = !track.enabled);
    updateButtonColors();
}

function updateButtonColors() {
    const localStream = localVideo.srcObject;
    if (!localStream) return;

    const micEnabled = localStream.getAudioTracks().some(track => track.enabled);
    const camEnabled = localStream.getVideoTracks().some(track => track.enabled);

    if (micEnabled) {
        micButton.classList.add('enabled');
    } else {
        micButton.classList.remove('enabled');
    }

    if (camEnabled) {
        camButton.classList.add('enabled');
    } else {
        camButton.classList.remove('enabled');
    }
}

function endCall() {
    ws.send(JSON.stringify({ type: 'end_call' }));
    closeVideocall();
}

function closeVideocall() {
    ws.close();
    peerConnection.close();
    window.location.href = "/chats/";
}