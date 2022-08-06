import json
import os
from time import sleep
from typing import Literal, TypedDict, cast
import typer
import yaml
import docker
from pathlib import Path
from rich import print
import boto3
from cryptography.fernet import Fernet
import dsnparse

app = typer.Typer()

class UploadDict(TypedDict):
    name: str
    bucket: str

class PsqlUrlDict(TypedDict):
    uri: str
    name: str
    version: Literal[11, 12, 13, 14]

class ConfigDict(TypedDict):
    source: PsqlUrlDict
    destination: PsqlUrlDict
    transformers: list[str]
    upload: UploadDict
    skip: list[str]


CACHED_CONFIG: ConfigDict | None = None
CONFIG_FILE = os.environ.get('CONFIG_FILE', '')

def _read_config() -> ConfigDict:
    global CACHED_CONFIG
    global CONFIG_FILE

    if not CACHED_CONFIG:
        if not CONFIG_FILE:
            raise ValueError("Empty CONFIG_FILE")

        with open(f'./{CONFIG_FILE}') as stream:
            CACHED_CONFIG = cast(ConfigDict, yaml.safe_load(stream))

        CACHED_CONFIG['destination']['uri'] = resolve_env(CACHED_CONFIG['destination']['uri'])
        CACHED_CONFIG['source']['uri'] = resolve_env(CACHED_CONFIG['source']['uri'])
        CACHED_CONFIG['upload']['name'] = resolve_env(CACHED_CONFIG['upload']['name'])
        CACHED_CONFIG['upload']['bucket'] = resolve_env(CACHED_CONFIG['upload']['bucket'])

    return CACHED_CONFIG

def resolve_env(variable: str) -> str:
    try:
        if variable_at := variable.index('$') == 0:
            return os.environ[variable[variable_at:]]
    except ValueError:
        pass
    except KeyError:
        pass

    return variable

@app.command()
def dump(from_: str | None=None, transform: bool=True, dump_name: str='dump'):
    config = _read_config()
    psql_version = config['source']['version']

    if not from_:
        connection_string = config['source']['uri']
    else:
        connection_string = from_

    dumps_folder = str(Path('dumps').resolve())

    print(f"=> Creating dump of database ({dump_name})")

    skips = ' '.join([
        f'--exclude-table-data {table}'
        for table in config.get('skip', [])
    ])

    docker_client = docker.from_env()
    docker_client.containers.run(
        f"postgres:{psql_version}",
        f"pg_dump --rows-per-insert=1000 --create --disable-triggers --no-owner --clean --dbname={connection_string} {skips} --file=/dumps/{dump_name}.sql",
        auto_remove=True,
        network_mode='host',
        volumes={
            dumps_folder: {'bind': '/dumps/', 'mode': 'rw'}
        }
    )

    if transform:
        anonymise()


@app.command()
def upload(dump_name: str):
    print("=> Uploading to S3")
    config = _read_config()
    bucket = config['upload']['bucket']
    name = config['upload']['name']

    fernet = Fernet(os.environ['ENCRYPTION_KEY'])
    source_file = f'dumps/{dump_name}.sql'
    with open(source_file, "rb") as file:
        plain_text_data = file.read()

    encrypted_data = fernet.encrypt(plain_text_data)

    with open(source_file, "wb") as file:
        file.write(encrypted_data)

    s3 = boto3.client('s3')
    s3.upload_file(
        source_file,
        bucket,
        f'{name}.sql',
    )
    print("=> Upload done to S3")


@app.command()
def download(dump_name: str | None = None):
    config = _read_config()
    bucket = config['upload']['bucket']

    if not dump_name:
        dump_name = config['upload']['name']

    s3 = boto3.client('s3')
    dest_file = f'dumps/{dump_name}.sql'
    s3.download_file(
        bucket,
        f'{dump_name}.sql',
        dest_file
    )
    print(f"=> Download complete. Decrypting file.")

    fernet = Fernet(os.environ['ENCRYPTION_KEY'])
    with open(dest_file, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    with open(dest_file, "wb") as file:
        file.write(decrypted_data)

    print(f"=> Dump downloaded & ready.")


@app.command()
def anonymise():
    config = _read_config()
    psql_version = config['source']['version']
    docker_client = docker.from_env()

    loaded_transformers: list[str] = config.get('transformers', [])
    transformers_folder = str(Path('transformers').resolve())
    dumps_folder = str(Path('dumps').resolve())

    print("=> Restoring database in a temporary database to anonymise")
    temporary_database = None

    source_uri = config['source']['uri']
    parsed_uri = dsnparse.parse(source_uri)
    dbname = parsed_uri.paths[0]

    try:
        temporary_database = docker_client.containers.run(
            f"postgres:{psql_version}",
            name='temporary-restore-db',
            auto_remove=True,
            detach=True,
            ports={
                '5432/tcp': 3333,
            },
            volumes={
                dumps_folder: {'bind': '/dumps/', 'mode': 'rw'},
                transformers_folder: {'bind': '/transformers/', 'mode': 'rw'}
            },
            environment={
                'POSTGRES_USER': 'anonymise',
                'POSTGRES_DB': dbname,
                'POSTGRES_PASSWORD': 'anonymise',
            }
        )
        sleep(2)

        destination_port = temporary_database.attrs['HostConfig']['PortBindings']['5432/tcp'][0]['HostPort']
        anonymise_db_connection_string = f'postgres://anonymise:anonymise@127.0.0.1:{destination_port}/{dbname}'

        restore(
            to=anonymise_db_connection_string,
            name='dump'
        )

        files_arg: str = ''
        for name in loaded_transformers:
            files_arg += f'-f {name} '

        print("=> Running transformers")
        temporary_database.exec_run(
            f'psql -U anonymise -d {dbname} -q -f functions.sql {files_arg} -f drop-functions.sql',
            environment={
                'PGPASSWORD': 'anonymise'
            },
            workdir="/transformers",
            demux=True
        )

        dump(
            from_=anonymise_db_connection_string,
            transform=False,
            dump_name="anonymised"
        )
    finally:
        if temporary_database:
            temporary_database.remove(force=True)


@app.command()
def restore(to: str | None = None, name: str | None = None, *, force_download: bool = False):
    config = _read_config()
    psql_version = config['destination']['version']

    if not to:
        connection_string = config['destination']['uri']
    else:
        connection_string = to

    if not name:
        name = config['upload']['name']

    if force_download or not Path(f'dumps/{name}.sql').exists():
        print(f"=> Downloading latest dump")
        download(name)
    else:
        print(f"=> Re-using already downloaded dump")

    docker_client = docker.from_env()

    dumps_folder = str(Path('dumps').resolve())
    transformers_folder = str(Path('transformers').resolve())

    dbname = config['destination']['name']

    print(f"=> Starting restore ({name})")

    try:
        docker_client.containers.run(
            f"postgres:{psql_version}",
            f'psql -c "DROP DATABASE IF EXISTS {dbname} WITH (FORCE);" -f /dumps/{name}.sql --dbname={connection_string}',
            auto_remove=True,
            network_mode='host',
            name="restore-db",
            volumes={
                dumps_folder: {'bind': '/dumps/', 'mode': 'rw'},
                transformers_folder: {'bind': '/transformers/', 'mode': 'rw'}
            }
        )
        # print('Logs', logs)
    finally:
        try:
            restore_db = docker_client.containers.get("restore-db")
            restore_db.remove(force=True)
        except docker.errors.NotFound:
            pass


def create_staging_services_list(connection_data: dict):
    username = connection_data['username']
    password = connection_data['password']

    url = f'postgresql://{username}:{password}@127.0.0.1:7777/pastaportobackend'
    return [
        ('pycon-config.yaml', url),
        ('users-config.yaml', url),
        ('association-config.yaml', url),
    ]


SERVICES = [
    ('pycon-config.yaml', "postgresql://pycon:pycon@127.0.0.1:15501/restoreuser"),
    ('users-config.yaml', "postgresql://users:users@127.0.0.1:15500/restoreuser"),
    ('association-config.yaml', "postgresql://association:association@127.0.0.1:15503/restoreuser"),
]

@app.command()
def restore_local(*, force_download: bool = False):
    global CONFIG_FILE
    global CACHED_CONFIG

    for config, url in SERVICES:
        CONFIG_FILE = config
        CACHED_CONFIG = None

        restore(
            to=url,
            force_download=force_download
        )

@app.command()
def restore_staging(*, force_download: bool = False):
    global CONFIG_FILE
    global CACHED_CONFIG

    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(
        SecretId='/pythonit/pastaporto/common/database'
    )
    connection_data = json.loads(secret['SecretString'])

    STAGING_SERVICES = create_staging_services_list(connection_data)

    for config, url in STAGING_SERVICES:
        CONFIG_FILE = config
        CACHED_CONFIG = None

        restore(
            to=url,
            force_download=force_download
        )


if __name__ == '__main__':
    app()
