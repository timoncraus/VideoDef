CREATE OR REPLACE FUNCTION check_unique_puzzle_name_grid_per_user()
RETURNS TRIGGER AS $$
DECLARE
    target_user_id character varying(7);
    existing_puzzle_count INTEGER;
BEGIN
    -- Определяем пользователя для текущей вставляемой/обновляемой записи
    SELECT ug.user_id
    INTO target_user_id
    FROM game_usergame ug
    WHERE ug.game_id = NEW.game_id;

    -- Выполняем проверку уникальности, только если имя или размер менялись (или при INSERT)
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND (NEW.name IS DISTINCT FROM OLD.name OR NEW.grid_size IS DISTINCT FROM OLD.grid_size)) THEN

        -- Ищем существующий пазл с таким же именем и размером сетки для текущего пользователя,
        -- исключая текущую строку (важно для UPDATE)
        SELECT COUNT(*)
        INTO existing_puzzle_count
        FROM game_userpuzzle up
        JOIN game_usergame ug ON up.game_id = ug.game_id
        WHERE up.name = NEW.name
          AND up.grid_size = NEW.grid_size
          AND ug.user_id = target_user_id
          AND up.game_id <> NEW.game_id;

        IF existing_puzzle_count > 0 THEN
            RAISE EXCEPTION 'Пазл с названием "%" и размером сетки %x% уже существует.', NEW.name, NEW.grid_size, NEW.grid_size
        END IF;

    END IF;

    -- Если дубликатов у этого пользователя нет, разрешаем операцию
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Удаляем триггер на случай повторного запуска скрипта
DROP TRIGGER IF EXISTS unique_puzzle_name_grid_per_user_trigger ON game_userpuzzle;

-- Создаем триггер, который вызывает функцию
CREATE TRIGGER unique_puzzle_name_grid_per_user_trigger
BEFORE INSERT OR UPDATE ON game_userpuzzle
FOR EACH ROW
EXECUTE FUNCTION check_unique_puzzle_name_grid_per_user();

-- Обновляем комментарии
COMMENT ON FUNCTION check_unique_puzzle_name_grid_per_user() IS 'Проверяет уникальность комбинации имени и размера сетки для пазла в рамках одного пользователя перед вставкой или обновлением.';