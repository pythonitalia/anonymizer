import subprocess
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
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from pathlib import Path
from azure.mgmt.containerinstance import ContainerInstanceManagementClient

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
        CACHED_CONFIG['upload']['source'] = resolve_env(CACHED_CONFIG['upload']['source'])

    return CACHED_CONFIG

def resolve_env(variable: str) -> str:
    try:
        if variable_at := variable.index('$') == 0:
            var_name = variable[variable_at:]
            return os.environ[var_name]
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
    source = config['upload']['source']
    bucket = config['upload']['bucket']

    if not dump_name:
        dump_name = config['upload']['name']

    dest_file = f'dumps/{dump_name}.sql'
    file_name = f'{dump_name}.sql'

    Path("dumps").mkdir(exist_ok=True)
    encryption_key = os.environ.get('ENCRYPTION_KEY', '')

    if source == 's3':
        s3 = boto3.client('s3')
        s3.download_file(
            bucket,
            file_name,
            dest_file
        )
    elif source == 'azure':
        account_url = f"https://{bucket}.blob.core.windows.net"
        blob_service_client = BlobServiceClient(account_url, credential=DefaultAzureCredential())
        blob_client = blob_service_client.get_blob_client(container='data', blob=file_name)
        with open(dest_file, 'wb') as open_file:
            open_file.write(blob_client.download_blob().readall())

        vault = get_azure_vault()
        encryption_key = vault.get_secret('encryption-key').value

    print(f"=> Download complete. Decrypting file.")

    fernet = Fernet(encryption_key)
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

    dumps_folder = str(Path('dumps').resolve())
    transformers_folder = str(Path('transformers').resolve())

    dbname = config['destination']['name']

    print(f"=> Starting restore ({name})")

    try:
        if is_azure():
            subprocess.run(
                f'psql -c "DROP DATABASE IF EXISTS {dbname} WITH (FORCE);" -f /app/dumps/{name}.sql --dbname={connection_string}',
                shell=True
            )
        else:
            docker_client = docker.from_env()
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
        if is_azure():
            return

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


def create_azure_staging_services_list():
    vault = get_azure_vault()

    db_username = vault.get_secret('db-root-username').value
    db_password = vault.get_secret('db-root-password').value
    host = vault.get_secret('host').value

    connection_url = f"postgresql://{db_username}:{db_password}@{host}:5432/postgres?sslmode=require"

    return [
        ('pycon-config.yaml', connection_url),
        ('users-config.yaml', connection_url),
        ('association-config.yaml', connection_url),
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


@app.command()
def restore_azure_staging_local():
    global CONFIG_FILE
    global CACHED_CONFIG

    # azure doesn't support docker-in-docker
    # so we start a local postgres server in the container
    subprocess.run(
        'service postgresql start',
        shell=True,
    )

    staging_services = create_azure_staging_services_list()

    for config, url in staging_services:
        CONFIG_FILE = config
        CACHED_CONFIG = None

        restore(
            to=url,
            force_download=True
        )

    print('Done!')


@app.command()
def restore_azure_staging():
    print('=> Starting restore job on Azure ACI...')

    aci_client = ContainerInstanceManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.getenv('AZURE_SUBSCRIPTION_ID')
    )
    poll = aci_client.container_groups.begin_start("anonymizer", "anonymizer-restore-data-job")
    poll.wait()

    print(f'=> Restore completed! Status: {poll.status()}')


def get_azure_vault():
    return SecretClient(vault_url="https://staging-database.vault.azure.net/", credential=DefaultAzureCredential())


def is_azure():
    config = _read_config()
    source = config['upload']['source']
    return source == 'azure'


if __name__ == '__main__':
    app()
