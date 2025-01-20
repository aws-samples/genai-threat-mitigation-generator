#!/usr/bin/env python

import os
import sys

sys.path.append(os.environ.get("LAMBDA_RUNTIME_DIR"))
sys.path.append("/opt/python")

import asyncio
import boto3
from botocore.client import Config
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from vectorstore_common.rds_sqlalchemy import RdsSqlAlchemy
from langchain_core.prompts import PromptTemplate
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain.chains import RetrievalQA
from langchain_postgres.vectorstores import PGVector, DistanceStrategy
from pydantic import BaseModel
from prompt_templates import prompt_templates

engine = RdsSqlAlchemy.engine_from_iam_credentials(
    os.environ.get("DB_NAME"),
    os.environ.get("DB_HOST"),
    os.environ.get("DB_USER"),
    async_mode=True,
)

bedrock_config = Config(
    connect_timeout=120,
    read_timeout=120,
    retries={"max_attempts": 5, "mode": "standard"},
)

bedrock_client = boto3.client(service_name="bedrock-runtime", config=bedrock_config)
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0", client=bedrock_client
)
s3_client = boto3.client("s3")

s3_bucket = os.environ.get("S3_BUCKET")
modelId = "anthropic.claude-3-sonnet-20240229-v1:0"

vectorstore = PGVector(
    embeddings=embeddings,
    connection=engine,
    distance_strategy=DistanceStrategy.COSINE,
)

app = FastAPI()


async def process(input_text: str, user_id: str, request_id: str):
    print(f"Processing query, user_id={user_id}, request_id={request_id}", flush=True)
    print("Building LLM...")

    llm = ChatBedrock(model_id=modelId, client=bedrock_client)
    llm.model_kwargs = {"temperature": 0.1, "max_tokens": 100000}

    # run X tasks at once, do not start X+1 if previous are not processed yet
    sem = asyncio.Semaphore(2)
    # single bedrock request at once to avoid rate limit
    lock = asyncio.Lock()

    async def create_events_stream(template, index):
        print(f"Requesting semaphore #{index}")
        # acquire the semaphore - will be released once streaming is done
        await sem.acquire()
        print(f"Acquired semaphore #{index}")

        # single bedrock request at once to avoid rate limit
        async with lock:
            print(f"Acquired lock #{index}")
            await asyncio.sleep(index)
            print(f"Delay done #{index}")

            prompt = PromptTemplate(
                template=template, input_variables=["context", "question"]
            )
            chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5, "include_metadata": True},
                ),
                chain_type_kwargs={"prompt": prompt},
            )
            return chain.astream_events(input_text, version="v2")

    result = ""
    error = ""
    tasks = [
        asyncio.create_task(create_events_stream(template, index))
        for index, template in enumerate(prompt_templates)
    ]
    try:
        for index, task in enumerate(tasks):
            print(f"Awaiting task #{index}...")
            await asyncio.wait_for(task, timeout=60.0)
            query = task.result()

            print(f"Processing task #{index}...")
            async for chunk in query:
                if "chunk" in chunk.get("data", {}):
                    content = chunk["data"]["chunk"].content
                    if content:
                        result += content
                        yield "data: " + json.dumps({"content": str(content)}) + "\n\n"
            yield "data: " + json.dumps({"content": str("\n\n")}) + "\n\n"

            # release semaphore we acquired earlier
            print(f"Releasing semaphore #{index}")
            sem.release()
    except Exception as e:
        error = str(e)
        print(f"Error: {e}", flush=True)
        yield "event: internal error \n\n"
        for task in tasks:
            task.cancel()

    print("Result:", flush=True)
    print(result, flush=True)

    yield "event: success \n\n"

    async def upload(key: str, text: str):
        if not text:
            return

        s3_client.put_object(Body=text, Bucket=s3_bucket, Key=key)

    await asyncio.gather(
        asyncio.create_task(upload(f"{user_id}/{request_id}/input.txt", input_text)),
        asyncio.create_task(upload(f"{user_id}/{request_id}/error.txt", error)),
        asyncio.create_task(upload(f"{user_id}/{request_id}/output.txt", result)),
    )


class Event(BaseModel):
    content: str


@app.get("/")
def healthcheck():
    return JSONResponse({"Status": "OK"}, 200)


@app.post("/")
def handler(request: Request, event: Event):
    context = json.loads(request.headers.get("x-amzn-request-context"))
    print(event, context)

    user_id = (
        context.get("authorizer", {})
        .get("iam", {})
        .get("userId", ":unknown")
        .split(":")
        .pop()
    )
    request_id = context.get("requestId", "")

    return StreamingResponse(
        process(input_text=event.content, user_id=user_id, request_id=request_id),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
