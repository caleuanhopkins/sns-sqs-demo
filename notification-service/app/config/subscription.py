import os
import boto3
import logging
from typing import Optional

endpoint_url = "http://host.docker.internal:4566"
sns_topic = "arn:aws:sns:us-east-1:000000000000:messages"


class SubscriptionManager(object):
    """
    Class to create and delete SNS subscriptions for an endpoint.
    """

    _subscription_arn: Optional[str]

    def __init__(self, endpoint: str):
        self._subscription_arn = None
        self._endpoint = endpoint

    @property
    def subscription_arn(self) -> str:
        return self._subscription_arn

    @subscription_arn.setter
    def subscription_arn(self, arn: str):
        self._subscription_arn = arn

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def create_subscription(self):
        """
        Subscribes an endpoint of this app to an SNS topic.

        :return: None
        """
        logging.info("Subscribing to SNS")

        # Initialize the AWS clients
        sns = boto3.client("sns", region_name="us-east-1", endpoint_url=endpoint_url)

        response = sns.subscribe(
            TopicArn=sns_topic,
            Protocol="http",
            Endpoint="http://host.docker.internal:8001/receive-message",
        )
        print("SUBSCRIBE RESPONSE\n", response)
        logging.info("CREATING SUBSCRIPTION")
        self._subscription_arn = response["SubscriptionArn"]

    def delete_subscription(self):
        """
        Deletes the endpoint subscription.

        :return: None
        """
        logging.info("Unsubscribing from SNS")
        sns = boto3.client("sns", region_name="us-east-1", endpoint_url=endpoint_url)
        sns.unsubscribe(self.subscription_arn)

    def confirm_subscription(self, token: str):
        """
        Confirms the subscription to the topic, given the confirmation token.

        :param token:
        :return:
        """
        logging.info("Confirming Subscription")
        sns = boto3.client("sns", region_name="us-east-1", endpoint_url=endpoint_url)
        response = sns.confirm_subscription(TopicArn=sns_topic, Token=token)
        self._subscription_arn = response["SubscriptionArn"]
