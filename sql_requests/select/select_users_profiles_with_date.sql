SELECT role1.name, profile.first_name, 
	profile.last_name, profile.patronymic,
	user1.username, user1.date_registr
FROM account_user AS user1
JOIN account_profile AS profile ON (user1.profile_id = profile.id)
JOIN account_role AS role1 ON (profile.role_id = role1.id)
WHERE user1.date_registr > '2025-05-01'
	AND user1.date_registr < '2025-07-01'