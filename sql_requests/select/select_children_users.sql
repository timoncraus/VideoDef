SELECT profile.first_name, profile.last_name, profile.patronymic,
	child.name AS child_name, 
	child.date_birth AS child_date_birth
FROM child_child AS child
JOIN account_user AS user1 ON(child.user_id = user1.unique_id)
JOIN account_profile AS profile ON (user1.profile_id = profile.id)