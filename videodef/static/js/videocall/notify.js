const userId = document.getElementById("user-data").dataset.userId;
const notifySocket = new WebSocket(
    `ws://${window.location.host}/ws/notify/${user_id}/`
);
console.log("Соединение об уведомлении установлено: ", notifySocket);
notifySocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "incoming_call") {
        if (confirm(`Вам звонит ${data.from}. Принять звонок?`)) {
            notifySocket.send(
                JSON.stringify({ answer: "acceptance", room_name: data.room_name })
            );
            window.location.href = `/videocall/call/${data.room_name}/`;
        } else {
            notifySocket.send(
                JSON.stringify({ answer: "rejection", room_name: data.room_name })
            );
        }
    }
};