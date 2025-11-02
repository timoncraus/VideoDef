const viewOtherUserBox = document.getElementById("view-other-user-box");
const otherUserId = viewOtherUserBox.dataset.otherUserId;
const csrfToken = viewOtherUserBox.dataset.csrfToken;
document.getElementById("start-call-btn").onclick = () => {
    fetch("/videocall/start-call/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ receiver_id: otherUserId }),
        })
        .then((resp) => resp.json())
        .then((data) => {
            if (data.success) {
                window.location.href = `/videocall/call/${data.room_name}/`;
            }
        });
};