SELECT user1.username,
	resume.short_info, resume.status, 
	COALESCE(image_count.num, 0) AS image_count,
	COALESCE(v_type_count.num, 0) AS v_type_count,
	COALESCE(doc_count.num, 0) AS doc_count,
	COALESCE(ver_doc_count.num, 0) AS ver_doc_count
FROM resume_resume AS resume
JOIN account_user AS user1 ON(resume.user_id = user1.unique_id)
LEFT JOIN (
	SELECT image.resume_id, COUNT(1) AS num
	FROM resume_resumeimage AS image
	GROUP BY image.resume_id
) AS image_count ON(resume.id = image_count.resume_id)
LEFT JOIN (
	SELECT v_type.resume_id, COUNT(1) AS num
	FROM resume_resume_violation_types AS v_type
	GROUP BY v_type.resume_id
) AS v_type_count ON(resume.id = v_type_count.resume_id)
LEFT JOIN (
	SELECT doc.resume_id, COUNT(1) AS num
	FROM resume_resume_documents AS doc
	GROUP BY doc.resume_id
) AS doc_count ON(resume.id = doc_count.resume_id)
LEFT JOIN (
	SELECT pinned_doc.resume_id, COUNT(1) AS num
	FROM resume_resume_documents AS pinned_doc
	JOIN document_document AS doc
		ON(pinned_doc.document_id = doc.id)
	JOIN document_documentverificationstatus AS status
		ON(doc.ver_status_id = status.id)
	WHERE status.name = 'На проверке'
	GROUP BY pinned_doc.resume_id
) AS ver_doc_count ON(resume.id = ver_doc_count.resume_id)

WHERE user1.username = 'w'