CREATE OR REPLACE FUNCTION check_unique_memory_game_name_pairs_per_user()
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

    -- Выполняем проверку уникальности, только если имя или количество пар менялись (или при INSERT)
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND (NEW.name IS DISTINCT FROM OLD.name OR NEW.pair_count IS DISTINCT FROM OLD.pair_count)) THEN

        -- Ищем существующую игру "Поиск пар" с таким же названием и количеством пар для текущего пользователя,
        -- исключая текущую строку (важно для UPDATE)
        SELECT COUNT(*)
        INTO existing_game_count
        FROM game_usermemorygame mg
        JOIN game_usergame ug ON mg.game_id = ug.game_id
        WHERE mg.name = NEW.name
          AND mg.pair_count = NEW.pair_count
          AND ug.user_id = target_user_id
          AND mg.game_id <> NEW.game_id;

        IF existing_game_count > 0 THEN
            RAISE EXCEPTION 'Игра "Поиск пар" с названием "%" и количеством пар "%" уже существует.', NEW.name, NEW.pair_count;
        END IF;

    END IF;

    -- Если дубликатов у этого пользователя нет, разрешаем операцию
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Удаляем триггер на случай повторного запуска скрипта
DROP TRIGGER IF EXISTS unique_memory_game_name_pairs_per_user_trigger ON game_usermemorygame;

-- Создаем триггер, который вызывает функцию
CREATE TRIGGER unique_memory_game_name_pairs_per_user_trigger
BEFORE INSERT OR UPDATE ON game_usermemorygame
FOR EACH ROW
EXECUTE FUNCTION check_unique_memory_game_name_pairs_per_user();

COMMENT ON FUNCTION check_unique_memory_game_name_pairs_per_user() IS 'Проверяет уникальность комбинации названия и количества пар для игры "Поиск пар" в рамках одного пользователя перед вставкой или обновлением.';