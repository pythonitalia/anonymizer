UPDATE grants_grant
SET
    name = random_first_name(),
    full_name = random_first_name() || ' ' || random_last_name(),
    occupation = 'other',
    grant_type = 'diversity',
    python_usage = random_text(),
    been_to_other_events = random_text(),
    interested_in_volunteering = 'no',
    why = random_text(),
    notes = random_text(),
    travelling_from = random_text();
