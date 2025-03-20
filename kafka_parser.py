# File: kafka_parser.py
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
from datetime import datetime


time_format = "%Y-%m-%d %H:%M:%S"


def parse_messages(topic, messages):
    ret_json = {}
    container_json = {}
    artifact_list = []

    ret_json["container"] = container_json
    ret_json["artifacts"] = artifact_list

    name = f"Messages ingested from {topic} at {datetime.now().strftime(time_format)}"

    container_json["name"] = name
    container_json["description"] = "Some messages from Kafka"
    container_json["run_automation"] = False

    count = 0
    num_artifacts = len(messages)
    for message in messages:
        artifact_json = {}
        artifact_list.append(artifact_json)

        artifact_json["source_data_identifier"] = "{}:{}".format(message["partition"], message["offset"])
        artifact_json["cef"] = {"message": message["message"]}
        artifact_json["name"] = message["message"][:100]

        if count < num_artifacts - 1:
            artifact_json["run_automation"] = False

        count += 1

    return [ret_json]
