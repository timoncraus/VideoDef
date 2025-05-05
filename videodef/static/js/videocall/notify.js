const notifySocket = new WebSocket(`ws://${window.location.host}/ws/notify/${user_id}/`);
notifySocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'incoming_call') {
        if (confirm(`Вам звонит ${data.from}. Принять звонок?`)) {
            window.location.href = `/videocall/call/${data.room_name}/`;
        }
    }
};