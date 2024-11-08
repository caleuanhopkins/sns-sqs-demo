# app/main.py
from fastapi import FastAPI, HTTPException
import boto3
import asyncio
import json
import os
import logging
import mysql.connector


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

endpoint_url = "http://host.docker.internal:4566"

# Initialize the AWS clients
sqs_client = boto3.client("sqs", region_name="us-east-1", endpoint_url=endpoint_url)

# Dictionary to store SNS topics and their corresponding SQS queues
QUEUES = {
    # listings_queue": "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/listings",
    "messages_queue": "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/messages",
}


def read_from_sqs(queue_url: str):
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=10
            )
            messages = response.get("Messages", [])
            if messages:
                for message in messages:
                    logger.info(f"Received message from {queue_url}: {message['Body']}")
                    dbrun = DatabaseProcess(message["Body"])
                    dbrun.run()
                    sqs_client.delete_message(
                        QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
                    )
                    logger.info(f"Deleted message from {queue_url}")
            else:
                logger.info(f"No messages in the queue {queue_url}.")
        except Exception as e:
            logger.error(f"Error reading from SQS: {str(e)}")


class DatabaseProcess:
    def __init__(self, message):
        logger.info("db init")
        self.message = json.loads(message)

    def run(self, *args, **kwargs):
        logger.info("running db insert")
        insert_query = """
        INSERT INTO messages (client, message)
        VALUES (%s, %s)
        """
        values = self.message["client"], self.message["message"]
        try:
            logger.info("trying to execute db qquery")
            cursor.execute(insert_query, values)
            mydb.commit()
        except mysql.connector.Error as err:
            logger.info("db error")
            raise HTTPException(status_code=400, detail=f"Error: {err}")

        return {"message": "message inserted successfully"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up and initiating SQS polling")

    for queue_url in QUEUES.values():
        read_from_sqs(queue_url)


mydb = mysql.connector.connect(
    host="dbpubsub", user="root", password="root", database="snsdb"
)

# Create a cursor object
cursor = mydb.cursor()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
