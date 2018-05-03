# --
# File: kafka_connector.py
#
# Copyright (c) 2017-2018 Splunk Inc.
#
# SPLUNK CONFIDENTIAL – Use or disclosure of this material in whole or in part
# without a valid written license from Splunk Inc. is PROHIBITED.
# --


def parse_messages(topic, message_dict):

    ret_json = {}
    container_json = {}
    artifact_list = []

    ret_json['container'] = container_json
    ret_json['artifacts'] = artifact_list

    name = '{0} {1}'.format(topic, min(message_dict.keys()))
    if len(message_dict) > 1:
        name = '{0}  - {1}'.format(name, max(message_dict.keys()))

    container_json['name'] = name
    container_json['description'] = "A message from Kafka"
    container_json['run_automation'] = False

    count = 0
    num_artifacts = len(message_dict)
    for offset, message in message_dict.iteritems():

        artifact_json = {}
        artifact_list.append(artifact_json)

        artifact_json['source_data_identifier'] = offset
        artifact_json['cef'] = {'message': message}
        artifact_json['name'] = message[:100]

        if count < num_artifacts - 1:
            artifact_json['run_automation'] = False

        count += 1

    return [ret_json]
