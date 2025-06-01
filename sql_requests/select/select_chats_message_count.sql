SELECT chat.id, user1.username, user2.username, 
	COUNT(1) AS message_count
FROM chat_message AS msg
JOIN chat_smallchat AS chat ON(msg.chat_id = chat.id)
JOIN account_user AS user1 ON(chat.user1_id = user1.unique_id)
JOIN account_user AS user2 ON(chat.user2_id = user2.unique_id)
GROUP BY chat.id, user1.username, user2.username