# app/main.py
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    APIRouter,
    Request,
)
import boto3
import asyncio
import json
import os
import logging
from fastapi.responses import JSONResponse
from config import SUBSCRIBER


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
    "listings_queue": "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/listings",
    "messages_queue": "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/messages",
}

connected_clients = set()

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.get("/healthcheck")
async def health():
    response = JSONResponse(content="OK!", status_code=200)
    return response


async def sendMsg(message: any):
    await manager.broadcast(message)


def handlesub(**kwargs):
    logger.info(kwargs)
    try:
        if "Type" in kwargs and kwargs["Type"] == "SubscriptionConfirmation":
            SUBSCRIBER.confirm_subscription(kwargs["Token"])
        else:
            logging.info("NOTIFICATION_RECEIVED")
            asyncio.create_task(sendMsg(json.dumps(kwargs)))
            # Do something interesting with the message. . .
        return True

    except Exception as e:
        logger.error("Subscriber fail! %s" % str(e))
        return False


@router.post("/receive-message")
async def receive_view(request: Request) -> JSONResponse:

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="cannot_parse_request_body")
    handler = handlesub(**dict(payload))

    if handler:
        logger.info("handled notification, yay!")
        response = JSONResponse(
            content={"message": "Message received!"}, status_code=200
        )
    else:
        logger.info("unhandled notification")
        response = JSONResponse(content={"message": "ERROR"}, status_code=500)

    return response


app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    # logger.info("Setting up SNS Subscription")
    logger.info("Starting up and initiating SQS polling")

    # for queue_url in QUEUES.values():
    # read_from_sqs(queue_url)


@app.on_event("shutdown")
def end_subscription():
    SUBSCRIBER.delete_subscription()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
