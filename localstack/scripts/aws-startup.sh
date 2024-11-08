#!/bin/bash

# SQS queus setup
awslocal sqs create-queue --queue-name listings --region=us-east-1
awslocal sqs create-queue --queue-name profiles --region=us-east-1
awslocal sqs create-queue --queue-name messages --region=us-east-1
awslocal sqs create-queue --queue-name database --region=us-east-1

# SNS topics setup
awslocal sns create-topic --name listings
awslocal sns create-topic --name messages

# Setup subscriptions
awslocal sns subscribe --topic-arn arn:aws:sns:us-east-1:000000000000:listings --protocol sqs --notification-endpoint arn:aws:sqs:us-east-1:000000000000:listings --attributes RawMessageDelivery=true 
awslocal sns subscribe --topic-arn arn:aws:sns:us-east-1:000000000000:messages --protocol sqs --notification-endpoint arn:aws:sqs:us-east-1:000000000000:messages --attributes RawMessageDelivery=true
awslocal sns subscribe --topic-arn arn:aws:sns:us-east-1:000000000000:messages --protocol sqs --notification-endpoint arn:aws:sqs:us-east-1:000000000000:database --attributes RawMessageDelivery=true
awslocal sns subscribe --topic-arn arn:aws:sns:us-east-1:000000000000:messages --protocol http --notification-endpoint http://host.docker.internal:8001/receive-message --attributes RawMessageDelivery=true