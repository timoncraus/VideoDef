const chatId = document.getElementById("chat-messages").dataset.chatId;
const chatSocket = new WebSocket(
    "ws://" + window.location.host + "/ws/chat/" + chatId + "/"
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    dateTimestamp = new Date(data.timestamp);
    document.querySelector("#chat-messages").innerHTML += `<div class="message ${
    data.message_type
  }">
            ${data.message}
            <div class="message-time">${formatTimestamp(
              dateTimestamp
            )} по мск</div>
        </div>`;
};

function formatTimestamp(date) {
    date = localizeTime(date);
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");

    return `${hours}:${minutes}`;
}

function getCurrTime() {
    date = new Date();
    date.setHours(date.getHours() - MINUTES_SHIFT / 60);
    date.setMinutes(date.getMinutes() + (MINUTES_SHIFT % 60));
    return date;
}

function localizeTime(date) {
    date.setHours(date.getHours() + 3);
    return date;
}

chatSocket.onclose = function(e) {
    console.error("Chat socket closed unexpectedly");
};

document.querySelector("#send-message-btn").onclick = function(e) {
    const messageInputDom = document.querySelector("#chat-message-input");
    const message = messageInputDom.value;

    chatSocket.send(JSON.stringify({ message: message }));

    messageInputDom.value = "";
};

function scrollToBottom() {
    var chatMessages = document.getElementById("chat-messages");
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function() {
    scrollToBottom();

    const chatMessages = document.getElementById("chat-messages");
    const observer = new MutationObserver(scrollToBottom);
    observer.observe(chatMessages, { childList: true });
});

function getDeclension(count, one, few, many) {
    if (count % 10 === 1 && count % 100 !== 11) return `${count} ${one} назад`;
    if (
        count % 10 >= 2 &&
        count % 10 <= 4 &&
        (count % 100 < 10 || count % 100 >= 20)
    )
        return `${count} ${few} назад`;
    return `${count} ${many} назад`;
}

function getSeconds(count) {
    return getDeclension(count, "секунду", "секунды", "секунд");
}

function getMinutes(count) {
    return getDeclension(count, "минуту", "минуты", "минут");
}

function getHours(count) {
    return getDeclension(count, "час", "часа", "часов");
}

function getDays(count) {
    return getDeclension(count, "день", "дня", "дней");
}

function getWeeks(count) {
    return getDeclension(count, "неделю", "недели", "недель");
}

function getMonths(count) {
    return getDeclension(count, "месяц", "месяца", "месяцев");
}

function getYears(count) {
    return getDeclension(count, "год", "года", "лет");
}

function statusTimeAgo(date, curr_utc_date, genderWord) {
    const diff = curr_utc_date - date;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);

    if (seconds < 1) {
        return "в сети";
    } else if (seconds < 60) {
        return genderWord + getSeconds(seconds);
    } else if (minutes < 60) {
        return genderWord + getMinutes(minutes);
    } else if (hours < 24) {
        return genderWord + getHours(hours);
    } else if (days < 2) {
        return "вчера";
    } else if (days < 7) {
        return genderWord + getDays(days);
    } else if (weeks < 4) {
        return genderWord + getWeeks(days);
    } else if (months < 12) {
        return genderWord + getMonths(months);
    } else {
        return getYears(years);
    }
}

MINUTES_SHIFT = 0;

function displayLastActiveDate() {
    const lastActiveDateStr = document
        .querySelector("#last-active-date")
        .getAttribute("data-date");
    const currDateStr = document
        .querySelector("#last-active-date")
        .getAttribute("data-curr-date");
    lastActiveDate = new Date(lastActiveDateStr);
    currDate = new Date(currDateStr);
    MINUTES_SHIFT = (new Date() - currDate) / 1000 / 60;

    const gender = document
        .querySelector("#last-active-date")
        .getAttribute("data-gender");
    genderWord = gender === "Женский" ? "была " : "был ";

    const formattedDate = statusTimeAgo(lastActiveDate, currDate, genderWord);
    document.querySelector("#last-active-formatted").textContent = formattedDate;
}
window.onload = displayLastActiveDate;