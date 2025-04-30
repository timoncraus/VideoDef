DELETE FROM public.document_documentverificationstatus;
INSERT INTO public.document_documentverificationstatus (id, name)
VALUES
    (1, 'На проверке'),
    (2, 'Проверено'),
	(3, 'Отказано');