# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import json
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8003",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

endpoint_url = "http://host.docker.internal:4566"

# Initialize the AWS clients
sns_client = boto3.client("sns", region_name="us-east-1", endpoint_url=endpoint_url)

engine = create_engine("mysql+pymysql://root:root@dbpubsub/snsdb")


# Define the SNS topics
TOPICS = {
    "listings_topic": "arn:aws:sns:us-east-1:000000000000:listings",
    "messages_topic": "arn:aws:sns:us-east-1:000000000000:messages",
}


class Notification(BaseModel):
    topic: str
    subject: str
    message: str


class Messages(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    client: str
    message: str


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@app.get("/messages/")
async def get_messages():
    with Session(engine) as session:
        messages = session.exec(select(Messages)).all()
        return messages


@app.post("/publish/")
async def publish_notification(notification: Notification):
    if notification.topic not in TOPICS:
        raise HTTPException(status_code=400, detail="Invalid topic")

    topic_arn = TOPICS[notification.topic]

    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps({"default": notification.message}),
            MessageStructure="json",
        )
        return {"message_id": response["MessageId"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
