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
If you want to restore all the databases you can use `restore_local`

### Restore everything in one-call

Use:

```shell
poetry run python main.py restore-local
```

### PyCon Backend

Use:

```shell
DESTINATION_DB_URL=postgresql://pycon:pycon@127.0.0.1:15501/restoreuser CONFIG_FILE=pycon-config.yaml poetry run python main.py restore
```

### Users Backend

Use:

```shell
DESTINATION_DB_URL=postgresql://users:users@127.0.0.1:15500/restoreuser CONFIG_FILE=users-config.yaml poetry run python main.py restore
```

### Association Backend

Use:

```shell
DESTINATION_DB_URL=postgresql://association:association@127.0.0.1:15503/restoreuser CONFIG_FILE=association-config.yaml poetry run python main.py restore
```

## Restore staging DB

Run

```shell
poetry run python main.py restore-staging
```

## Notes

By default `restore` will re-use the latest downloaded prod data. Use the flag `--force-download` if you want to force downloading the latest production data.

A fresh production data is generated every night. You can manually run the GitHub Action if you need new fresh data.
