CREATE OR REPLACE FUNCTION check_profile_data()
RETURNS TRIGGER AS $$
DECLARE
    valid_name_pattern CONSTANT TEXT := '^[A-Za-zА-Яа-яЁё]+$';  -- Регулярное выражение для проверки имени и фамилии
BEGIN
    -- Проверка имени
    IF NEW.first_name !~ valid_name_pattern THEN
        RAISE EXCEPTION 'Имя должно содержать только буквы';
    END IF;

    -- Проверка фамилии
    IF NEW.last_name !~ valid_name_pattern THEN
        RAISE EXCEPTION 'Фамилия должна содержать только буквы';
    END IF;

    -- Проверка даты рождения (не может быть в будущем)
    IF NEW.date_birth > CURRENT_DATE THEN
        RAISE EXCEPTION 'Дата рождения не может быть в будущем';
    END IF;

    -- Проверка возраста (не более 120 лет)
    IF EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM NEW.date_birth) > 120 THEN
        RAISE EXCEPTION 'Возраст не может превышать 120 лет';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_profile_data_trigger
BEFORE INSERT OR UPDATE ON profile  -- Замените на название вашей таблицы
FOR EACH ROW
EXECUTE FUNCTION check_profile_data();
