UPDATE users SET
    full_name = random_first_name() || ' ' || random_last_name(),
    name = random_first_name(),
    password = '!',
    email = random_email(),
    username = random_username(),
    jwt_auth_id = 1,
    date_birth = random_date_of_birth()
WHERE is_staff = false;
