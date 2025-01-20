import io
import json
import os
import boto3
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_postgres.vectorstores import PGVector
from urllib.parse import unquote_plus
from PyPDF2 import PdfReader

from vectorstore_common.rds_sqlalchemy import RdsSqlAlchemy

boto3_bedrock = boto3.client("bedrock-runtime")
s3 = boto3.client("s3")
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0", client=boto3_bedrock
)
engine = RdsSqlAlchemy.engine_from_secret_manager_credentials(
    os.environ.get("DB_HOST"), os.environ.get("DB_SECRET")
)

text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " "],
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)


def handler(event, context):
    print(json.dumps(event))
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        print(f"Processing: {bucket}, Key: {key}")
        s3_object = s3.get_object(Bucket=bucket, Key=key)
        pdf = io.BytesIO(s3_object["Body"].read())

        print(f"File retrieved")
        document = "".join([page.extract_text() for page in PdfReader(pdf).pages])
        print(f"Document extracted")
        text_chunks = text_splitter.split_text(document)
        print(f"Document chunked")

        vectordb = PGVector(
            connection=engine, embeddings=embeddings, create_extension=False
        )
        print(f"Vector store created")
        vectordb.add_texts(text_chunks)

        s3.delete_object(Bucket=bucket, Key=key)
