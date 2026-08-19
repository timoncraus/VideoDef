CREATE OR REPLACE FUNCTION check_unique_sound_loto_name_rounds_per_user()
RETURNS TRIGGER AS $$
DECLARE
    target_user_id character varying(7);
    existing_game_count INTEGER;
BEGIN
    -- Определяем пользователя для текущей вставляемой/обновляемой записи
    SELECT ug.user_id
    INTO target_user_id
    FROM game_usergame ug
    WHERE ug.game_id = NEW.game_id;

    -- Выполняем проверку уникальности, только если имя или количество раундов менялись (или при INSERT)
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND (NEW.name IS DISTINCT FROM OLD.name OR NEW.rounds_count IS DISTINCT FROM OLD.rounds_count)) THEN

        -- Ищем существующую игру "Звуковое лото" с таким же названием и количеством раундов для текущего пользователя,
        -- исключая текущую строку (важно для UPDATE)
        SELECT COUNT(*)
        INTO existing_game_count
        FROM game_usersoundloto sl
        JOIN game_usergame ug ON sl.game_id = ug.game_id
        WHERE sl.name = NEW.name
          AND sl.rounds_count = NEW.rounds_count
          AND ug.user_id = target_user_id
          AND sl.game_id <> NEW.game_id;

        IF existing_game_count > 0 THEN
            RAISE EXCEPTION 'Игра "Звуковое лото" с названием "%" и количеством раундов "%" уже существует.', NEW.name, NEW.rounds_count;
        END IF;

    END IF;

    -- Если дубликатов у этого пользователя нет, разрешаем операцию
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Удаляем триггер на случай повторного запуска скрипта
DROP TRIGGER IF EXISTS unique_sound_loto_name_rounds_per_user_trigger ON game_usersoundloto;

-- Создаем триггер, который вызывает функцию
CREATE TRIGGER unique_sound_loto_name_rounds_per_user_trigger
BEFORE INSERT OR UPDATE ON game_usersoundloto
FOR EACH ROW
EXECUTE FUNCTION check_unique_sound_loto_name_rounds_per_user();

COMMENT ON FUNCTION check_unique_sound_loto_name_rounds_per_user() IS 'Проверяет уникальность комбинации названия и количества раундов для игры "Звуковое лото" в рамках одного пользователя перед вставкой или обновлением.';