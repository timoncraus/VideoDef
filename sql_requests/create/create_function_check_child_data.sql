CREATE OR REPLACE FUNCTION check_child_data()
RETURNS TRIGGER AS $$
DECLARE
    valid_name_pattern CONSTANT TEXT := '^[A-Za-zА-Яа-яЁё]+$';
BEGIN
    IF NEW.name !~ valid_name_pattern THEN
        RAISE EXCEPTION 'Имя ребенка должно содержать только буквы';
    END IF;
    IF NEW.date_birth > CURRENT_DATE THEN
        RAISE EXCEPTION 'Дата рождения не может быть в будущем';
    END IF;
    IF EXTRACT(YEAR FROM CURRENT_DATE) 
		- EXTRACT(YEAR FROM NEW.date_birth) > 120 THEN
        RAISE EXCEPTION 'Возраст ребенка не может превышать 120 лет';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_child_data_trigger
BEFORE INSERT OR UPDATE ON child_child
FOR EACH ROW
EXECUTE FUNCTION check_child_data();
