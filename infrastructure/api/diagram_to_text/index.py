#!/usr/bin/env python
import base64
import os
import sys
from typing import Union

sys.path.append(os.environ.get("LAMBDA_RUNTIME_DIR"))
sys.path.append("/opt/python")

import asyncio
import boto3
from botocore.client import Config
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate

from pydantic import BaseModel

bedrock_config = Config(
    connect_timeout=120,
    read_timeout=120,
    retries={"max_attempts": 5, "mode": "standard"},
)

bedrock_client = boto3.client(service_name="bedrock-runtime", config=bedrock_config)
s3_client = boto3.client("s3")

s3_bucket = os.environ.get("S3_BUCKET")
modelId = "anthropic.claude-3-sonnet-20240229-v1:0"

app = FastAPI()


async def process(image_base64: str, user_id: str, request_id: str):
    print(f"Processing query, user_id={user_id}, request_id={request_id}", flush=True)

    chat = ChatBedrock(
        model_id=modelId,
        client=bedrock_client,
        model_kwargs={"temperature": 0.1, "top_p": 0.1},
    )
    prompt = PromptTemplate.from_template(
        """You are a cloud infrastructure specialist, explaining Amazon Web Service (AWS) architectural diagrams to
        business people and engineers in a meeting. Based on a provided image, describe each individual component
        and its relations and interactions with other components. This is very important. After this, provide a
        summary of the architecture, including its purpose. Do not use conditional terms like “probably”, “maybe”,
        “likely” and similar, as this does not build trust. If you are unsure about something, don’t mention it. Be
        straight to the point, do not start your response by words like “Sure, here is a...".

        After this please write me chapter describing flow of the data in details
        """.replace(
            "\n", " "
        )
    )
    content = [
        {"type": "text", "text": prompt.format()},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_base64,
            },
        },
    ]
    message_list = [{"role": "user", "content": content}]

    query = chat.astream_events(message_list, version="v2")

    result = ""
    error = ""
    try:
        print(f"Processing query...")
        async for chunk in query:
            if "chunk" in chunk.get("data", {}):
                content = chunk["data"]["chunk"].content
                if content:
                    result += content
                    yield "data: " + json.dumps({"content": str(content)}) + "\n\n"
        yield "data: " + json.dumps({"content": str("\n\n")}) + "\n\n"
    except Exception as e:
        error = str(e)
        print(f"Error: {e}", flush=True)
        yield "event: internal error \n\n"

    print("Result:", flush=True)
    print(result, flush=True)

    yield "event: success \n\n"

    async def upload(key: str, body: Union[str, bytes]):
        if not body:
            return

        s3_client.put_object(Body=body, Bucket=s3_bucket, Key=key)

    await asyncio.gather(
        asyncio.create_task(
            upload(f"{user_id}/{request_id}/input.png", base64.b64decode(image_base64))
        ),
        asyncio.create_task(upload(f"{user_id}/{request_id}/error.txt", error)),
        asyncio.create_task(upload(f"{user_id}/{request_id}/output.txt", result)),
    )


class EventContent(BaseModel):
    name: str
    type: str
    data: str


class Event(BaseModel):
    content: EventContent


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
        process(
            image_base64=event.content.data, user_id=user_id, request_id=request_id
        ),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
