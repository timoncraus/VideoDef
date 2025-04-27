CREATE TRIGGER check_profile_data_trigger
BEFORE INSERT OR UPDATE ON account_profile
FOR EACH ROW
EXECUTE FUNCTION check_profile_data();
