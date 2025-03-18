# File: kafka_consts.py
#
# Copyright (c) 2017-2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
DEFAULT_TIMEOUT = 30

KAFKA_PRODUCER_CREATE_ERROR = "Could not connect Kafka producer to Kafka server: {0}"
KAFKA_PRODUCER_SEND_ERROR = "Kafka Producer failed to send message to Kafka server: {0}"
KAFKA_PRODUCER_NO_BROKERS_ERROR = (
    "Could not connect to Kafka on {0} due to:\n{1}. This is usually caused by the Kafka server not running or the port being closed"
)

KAFKA_WARNING_SOME_HOSTS_FAILED = "Connection to Kafka cluster successful, but connection to some hosts failed. See above."

KAFKA_TOPIC_NOT_FOUND = "The specified topic could not be found on the Kafka server"
KAFKA_TOPIC_INVALID_ERROR = (
    "The specified topic contains invalid characters. Topics can only contain numbers, letters, periods, hyphens, and underscores."
)

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
KAFKA_ERROR_SEND_FAILED = "{0} message{1} failed to send, see spawn logs"
KAKFA_ERROR_CONTAINER_COUNT = "Container count should be a positive integer"
KAFKA_ERROR_CONNECTIVITY_FAILED = "Could not connect to Kafka on {0} due to:\n{1}"
KAFKA_ERROR_TIMEOUT = "There was an issue sending data to Kafka - sending timed out"
KAFKA_ERROR_INVALID_PORT = "Could not connect to Kafka on {0} due to:\nInvalid port number: {1}"
KAFKA_ERROR_EMPTY_LIST = "Got an empty list as message to send. To send an empty list, try '[[]]'"
KAFKA_ERROR_PARSER_ARGS = "{0}: parse_messages() should take exactly 2 arguments, takes {1} instead"
KAFKA_ERROR_SSL_CONFIG = "To use SSL, at least one of cert_file, key_file, or ca_cert asset configuration parameters must be filled out"

KAFKA_TEST_CONNECTIVITY_FAILED = "Test Connectivity Failed"
KAFKA_TEST_CONNECTIVITY_PASSED = "Test Connectivity Passed"
KAFKA_TEST_PARSER = "Checking custom message parsing script - {0}"
KAFKA_TEST_MESSAGES = {9: "Ninth message", 10: "Tenth message"}
