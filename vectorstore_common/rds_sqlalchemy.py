import json
import boto3
from sqlalchemy import create_engine, URL, event
from sqlalchemy.ext.asyncio import create_async_engine

rds = boto3.client("rds")
secrets_manager = boto3.client("secretsmanager")

PORT = 5432


class RdsSqlAlchemy:

    @staticmethod
    def engine_from_iam_credentials(
        dbname: str, endpoint: str, username: str, port=PORT, async_mode=False
    ):
        token = rds.generate_db_auth_token(
            DBHostname=endpoint, Port=port, DBUsername=username
        )
        url = URL(
            drivername="postgresql+psycopg",
            username=username,
            password=token,
            port=port,
            query={
                "sslmode": "require",
            },
            host=endpoint,
            database=dbname,
        )
        engine = create_async_engine(url) if async_mode else create_engine(url)

        @event.listens_for(engine.sync_engine if async_mode else engine, "do_connect")
        def receive_do_connect(dialect, conn_rec, cargs, cparams):
            token = rds.generate_db_auth_token(
                DBHostname=endpoint, Port=port, DBUsername=username
            )
            cparams["password"] = token

        return engine

    @staticmethod
    def engine_from_secret_manager_credentials(
        endpoint: str, secret_arn: str, port=PORT, async_mode=False
    ):
        secret = secrets_manager.get_secret_value(SecretId=secret_arn)
        credentials = json.loads(secret["SecretString"])

        url = URL(
            drivername="postgresql+psycopg",
            username=credentials["username"],
            password=credentials["password"],
            port=port,
            query={
                "sslmode": "require",
            },
            host=endpoint,
            database=credentials["dbname"],
        )
        engine = create_async_engine(url) if async_mode else create_engine(url)

        return engine
