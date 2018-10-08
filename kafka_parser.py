# --
# File: kafka_parser.py
#
# Copyright (c) 2017-2018 Splunk Inc.
#
# SPLUNK CONFIDENTIAL - Use or disclosure of this material in whole or in part
# without a valid written license from Splunk Inc. is PROHIBITED.
# --

from datetime import datetime
time_format = '%Y-%m-%d %H:%M:%S'


def parse_messages(topic, messages):

    ret_json = {}
    container_json = {}
    artifact_list = []

    ret_json['container'] = container_json
    ret_json['artifacts'] = artifact_list

    name = 'Messages ingested from {0} at {1}'.format(topic, datetime.now().strftime(time_format))

    container_json['name'] = name
    container_json['description'] = "Some messages from Kafka"
    container_json['run_automation'] = False

    count = 0
    num_artifacts = len(messages)
    for message in messages:

        artifact_json = {}
        artifact_list.append(artifact_json)

        artifact_json['source_data_identifier'] = '{0}:{1}'.format(message['partition'], message['offset'])
        artifact_json['cef'] = {'message': message['message']}
        artifact_json['name'] = message['message'][:100]

        if count < num_artifacts - 1:
            artifact_json['run_automation'] = False

        count += 1

    return [ret_json]
