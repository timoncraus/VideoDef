SELECT user1.username, COUNT(1) AS count_videocalls
FROM videocall_videocall AS videocall
JOIN account_user AS user1 
	ON(videocall.caller_id = user1.unique_id
	   OR videocall.receiver_id = user1.unique_id)
GROUP BY user1.username