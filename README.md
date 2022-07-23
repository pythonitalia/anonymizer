## How to restore prod data locally

Requirements to restore production data:

- You will need the encryption key
- Name of the bucket where the data is stored
- An AWS account

You will need to set the following variables:

```shell
export BUCKET_NAME=<value here>
export ENCRYPTION_KEY=<value here>
```

Once you have the secrets, you have to:

1. Make sure you have PyCon databases running
2. Clone this repo
3. Run `poetry install`

Once setup you can run the `restore` command pointing to the database you want to restore.

### PyCon Backend

Use:

```shell
DESTINATION_DB_URL=postgresql://pycon:pycon@127.0.0.1:15501/pycon CONFIG_FILE=pycon-config.yaml poetry run python main.py restore
```

### Users Backend

Use:

```shell
DESTINATION_DB_URL=postgresql://users:users@127.0.0.1:15500/users CONFIG_FILE=users-config.yaml poetry run python main.py restore
```

### Association Backend

Use:

```shell
DESTINATION_DB_URL=postgresql://association:association@127.0.0.1:15503/association CONFIG_FILE=association-config.yaml poetry run python main.py restore
```

## Notes

The `restore` command will re-use the latest downloaded dump of the database.
If you want fresh data delete the `dumps` folder.
