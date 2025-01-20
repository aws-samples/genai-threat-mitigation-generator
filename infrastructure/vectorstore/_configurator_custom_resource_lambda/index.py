import json
import boto3
import os
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_postgres.vectorstores import PGVector
from psycopg import sql

from vectorstore_common.rds_sqlalchemy import RdsSqlAlchemy

engine = RdsSqlAlchemy.engine_from_secret_manager_credentials(
    os.environ.get("DB_HOST"), os.environ.get("DB_SECRET")
)

boto3_bedrock = boto3.client("bedrock-runtime")
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0", client=boto3_bedrock
)


def handler(event, context):
    print(json.dumps(event))

    base_response = {
        "LogicalResourceId": event.get("LogicalResourceId", None),
        "RequestId": event.get("RequestId", None),
        "StackId": event.get("StackId", None),
        "PhysicalResourceId": event.get("PhysicalResourceId", None),
    }
    success_response = {"Status": "SUCCESS", "Reason": "", **base_response}
    request_type = event.get("RequestType", None)
    vectorstore = PGVector(
        connection=engine,
        embeddings=embeddings,
        create_extension=True,
    )
    vectorstore.create_tables_if_not_exists()
    vectorstore.create_collection()

    database = event.get("ResourceProperties", {}).get("database", "postgres")
    username = event.get("ResourceProperties", {}).get("username", None)
    role = event.get("ResourceProperties", {}).get("role", "read_only")

    if not username:
        return success_response

    if role not in ["read_only", "read_write"]:
        return {
            "Status": "FAILED",
            "Reason": f"""Invalid role "{role}".""",
            **base_response,
        }

    raw_connection = engine.raw_connection()

    try:
        print(f"Configure user {username} with action {request_type}")
        cursor = raw_connection.cursor()

        current_user = cursor.execute(sql.SQL("SELECT current_user")).fetchone()[0]
        print(f"Current user: {current_user}")

        if request_type == "Delete":
            cursor.execute(
                sql.SQL("REVOKE rds_iam FROM {}").format(sql.Identifier(username))
            )

            cursor.execute(
                sql.SQL(
                    "REVOKE ALL ON TABLE public.langchain_pg_collection FROM {}"
                ).format(sql.Identifier(username))
            )
            cursor.execute(
                sql.SQL(
                    "REVOKE ALL ON TABLE public.langchain_pg_embedding FROM {}"
                ).format(sql.Identifier(username))
            )

            cursor.execute(
                sql.SQL(
                    "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {}"
                ).format(sql.Identifier(username))
            )
            cursor.execute(
                sql.SQL(
                    "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {}"
                ).format(sql.Identifier(username))
            )
            cursor.execute(
                sql.SQL(
                    "REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {}"
                ).format(sql.Identifier(username))
            )

            cursor.execute(
                sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(username), sql.Identifier(current_user)
                )
            )
            cursor.execute(
                sql.SQL("REASSIGN OWNED BY {} TO {}").format(
                    sql.Identifier(username), sql.Identifier(current_user)
                )
            )
            cursor.execute(
                sql.SQL("REVOKE postgres FROM {}").format(sql.Identifier(username))
            )

            cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(username)))
            cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(username)))

        else:
            cursor.execute(
                sql.SQL(
                    """
DO $$
BEGIN
CREATE ROLE {} WITH LOGIN;
EXCEPTION WHEN duplicate_object THEN RAISE NOTICE '%, skipping', SQLERRM USING ERRCODE = SQLSTATE;
END
$$;
            """
                ).format(sql.Identifier(username))
            )

            cursor.execute(
                sql.SQL(
                    "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {}"
                ).format(sql.Identifier(username))
            )
            cursor.execute(
                sql.SQL(
                    "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {}"
                ).format(sql.Identifier(username))
            )
            cursor.execute(
                sql.SQL(
                    "REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {}"
                ).format(sql.Identifier(username))
            )

            cursor.execute(
                sql.SQL("GRANT rds_iam TO {}").format(sql.Identifier(username))
            )
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(database), sql.Identifier(username)
                )
            )
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )
            cursor.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )

            if role == "read_write":
                cursor.execute(
                    sql.SQL(
                        "GRANT INSERT, UPDATE, DELETE ON public.langchain_pg_collection TO {}"
                    ).format(sql.Identifier(username))
                )
                cursor.execute(
                    sql.SQL(
                        "GRANT INSERT, UPDATE, DELETE ON public.langchain_pg_embedding TO {}"
                    ).format(sql.Identifier(username))
                )
        raw_connection.commit()
        cursor.close()
    except Exception as e:
        print(e, flush=True)
        raw_connection.rollback()
        raw_connection.close()
        return {"Status": "FAILED", "Reason": str(e), **base_response}

    raw_connection.close()
    return success_response
