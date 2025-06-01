DO $$
DECLARE
    r RECORD;
    truncate_sql TEXT := '';
BEGIN
    -- Собираем имена таблиц, кроме тех, что начинаются с 'django'
    FOR r IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename NOT LIKE 'django%'
			  OR tablename = 'django_admin_log'
    LOOP
        truncate_sql := truncate_sql || format('"%I", ', r.tablename);
    END LOOP;

    -- Если есть таблицы для очистки, удаляем последние ", " и выполняем TRUNCATE
    IF length(truncate_sql) > 0 THEN
        truncate_sql := left(truncate_sql, length(truncate_sql) - 2);
        EXECUTE format('TRUNCATE TABLE %s RESTART IDENTITY CASCADE;', truncate_sql);
    END IF;
END $$;
