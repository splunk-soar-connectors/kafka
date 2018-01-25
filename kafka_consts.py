# --
# File: kafka_consts.py
#
# Copyright (c) Phantom Cyber Corporation, 2017-2018
#
# This unpublished material is proprietary to Phantom Cyber.
# All rights reserved. The methods and
# techniques described herein are considered trade secrets
# and/or confidential. Reproduction or distribution, in whole
# or in part, is forbidden except by express written permission
# of Phantom Cyber.
#
# --

KAFKA_PRODUCER_CREATE_ERROR = "Could not connect Kafka producer to Kafka server: {0}"
KAFKA_PRODUCER_SEND_ERROR = "Kafka Producer failed to send message to Kafka server: {0}"
KAFKA_PRODUCER_NO_BROKERS_ERROR = "Could not connect to Kafka on {0} due to:\n{1}. This is usually caused by the Kafka server not running or the port being closed"

KAFKA_WARNING_SOME_HOSTS_FAILED = "Connection to Kafka cluster successful, but connection to some hosts failed. See above."

KAFKA_TOPIC_NOT_FOUND = "The specified topic could not be found on the Kafka server"
KAFKA_TOPIC_INVALID_ERROR = "The specified topic contains invalid characters. Topics can only contain numbers, letters, periods, hyphens, and underscores."

KAFKA_NO_MESSAGES = "No messages to ingest, taking no action"
KAFKA_USING_PARSER = "Using custom message parsing script - {0}"

KAFKA_SUCCESS_SEND = "Successfully sent data to Kafka"

KAFKA_ERROR_DATA_TYPE = "Invalid data_type given: {0}"
KAFKA_ERROR_BAD_TIMEOUT = "Timeout should not be negative"
KAFKA_ERROR_NO_OFFSET = "Kafka could not assign message to offset"
KAFKA_ERROR_MESSAGE_PARSER = "Got an exception in call to {0}: {1}"
KAFKA_ERROR_NO_PARTITION = "Kafka could not assign message to partition"
KAFKA_ERROR_BAD_JSON = "Supplied data could not be decoded as JSON: {0}"
KAKFA_ERROR_ARTIFACT_COUNT = "Artifact count should be a positive integer"
KAFKA_ERROR_SEND_FAILURES = "{0} message{1} failed to send, see spawn logs"
KAKFA_ERROR_CONTAINER_COUNT = "Container count should be a positive integer"
KAFKA_ERROR_COULD_NOT_CONNECT = "Could not connect to Kafka on {0} due to:\n{1}"
KAFKA_ERROR_TIMEOUT = "There was an issue sending data to Kafka - sending timed out"
KAFKA_ERROR_INVALID_PORT = "Could not connect to Kafka on {0} due to:\nInvalid port number: {1}"
KAFKA_ERROR_EMPTY_LIST = "Got an empty list as message to send. To send an empty list, try '[[]]'"
KAFKA_ERROR_PARSER_ARGS = "{0}: parse_messages() should take exactly 2 arguments, takes {1} instead"

KAFKA_TEST_CONNECTIVITY_FAILED = "Test Connectivity Failed"
KAFKA_TEST_CONNECTIVITY_PASSED = "Test Connectivity Passed"
KAFKA_TEST_PARSER = "Checking custom message parsing script - {0}"
KAFKA_TEST_MESSAGES = {9: "Ninth message", 10: "Tenth message"}
