# File: kafka_connector.py
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
#
#
# Phantom App imports
import imp
import inspect
import logging
import re
import traceback
from io import StringIO

import phantom.app as phantom
import simplejson as json
from kafka import KafkaConsumer, KafkaProducer, TopicPartition  # pylint: disable=E0611
from kafka.errors import KafkaTimeoutError, NoBrokersAvailable  # pylint: disable=E0401,E0611

# Imports local to this App
import kafka_consts as consts
from kafka_parser import parse_messages


logger = logging.getLogger("kafka")
log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.DEBUG)
logger.setLevel(logging.DEBUG)

KAFKA_PARSER_MODULE_NAME = "custom_parser"


# Define the App Class
class KafkaConnector(phantom.BaseConnector):
    ACTION_ID_TEST_CONNECTIVITY = "test_connectivity"
    ACTION_ID_POST_DATA = "post_data"
    ACTION_ID_ON_POLL = "on_poll"

    def __init__(self):
        # Call the BaseConnectors init first
        super().__init__()

        self._state = {}
        self._producer = None
        self._host_list = None
        self._client_args = None

    def initialize(self):
        self._state = self.load_state()

        config = self.get_config()

        self._host_list = config["hosts"].split(",")
        self._client_args = {"bootstrap_servers": self._host_list}

        sec_prot = "PLAINTEXT"
        if config.get("use_kerberos", False):
            sec_prot = "SASL_SSL" if config.get("use_ssl") else "SASL_PLAINTEXT"
            self._client_args.update({"sasl_mechanism": "GSSAPI"})
        if config.get("use_ssl"):
            if "cert_file" not in config and "key_file" not in config and "ca_cert" not in config:
                return self.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_SSL_CONFIG)
            if sec_prot == "PLAINTEXT":
                sec_prot = "SSL"
            if "cert_file" in config:
                self._client_args.update({"ssl_certfile": config["cert_file"]})
            if "key_file" in config:
                self._client_args.update({"ssl_keyfile": config["key_file"]})
            if "ca_cert" in config:
                self._client_args.update({"ssl_cafile": config["ca_cert"], "ssl_check_hostname": False})

        self._client_args.update({"security_protocol": sec_prot})

        try:
            if self.get_action_identifier() == self.ACTION_ID_POST_DATA:
                self._producer = KafkaProducer(**self._client_args)
        except Exception as e:
            self.save_progress(traceback.format_exc())
            return self.set_status(phantom.APP_ERROR, consts.KAFKA_PRODUCER_CREATE_ERROR.format(e))

        return phantom.APP_SUCCESS

    def finalize(self):
        self.save_state(self._state)
        return phantom.APP_SUCCESS

    def _test_connectivity(self, param):
        action_result = self.add_action_result(phantom.ActionResult(dict(param)))
        self.save_progress("Creating a temporary consumer to test connectivity")

        config = self.get_config()

        if int(config.get("timeout", 0)) < 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_BAD_TIMEOUT)

        try:
            KafkaConsumer(**self._client_args)
        except Exception as e:
            self.save_progress(consts.KAFKA_PRODUCER_CREATE_ERROR.format(e))
            self.save_progress(traceback.format_exc())
            for line in log_stream.getvalue().split("\n"):
                self.debug_print("KAFKA LOG: " + line)
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TEST_CONNECTIVITY_FAILED)

        if not self._check_hosts(self._host_list):
            self.save_progress(consts.KAFKA_WARNING_SOME_HOSTS_FAILED)

        parser = config.get("message_parser")

        if parser:
            parser_name = config["message_parser__filename"]

            self.save_progress(consts.KAFKA_TEST_PARSER.format(parser_name))

            message_parser = imp.new_module(KAFKA_PARSER_MODULE_NAME)

            try:
                exec(parser in message_parser.__dict__)

                num_args = len(inspect.getargspec(message_parser.parse_messages).args)
                if num_args != 2:
                    return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_PARSER_ARGS.format(parser_name, num_args))

                message_parser.parse_messages(config["topic"], consts.KAFKA_TEST_MESSAGES)

            except Exception as e:
                return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_MESSAGE_PARSER.format(parser_name, e))

        self.save_progress(consts.KAFKA_TEST_CONNECTIVITY_PASSED)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _save_container(self, container_dict):
        config = self.get_config()

        container = container_dict.get("container")

        container["label"] = config.get("ingest", {}).get("container_label")

        ret_val, message, container_id = self.save_container(container)

        if not ret_val:
            return ret_val, message

        artifacts = container_dict.get("artifacts")

        for artifact in artifacts:
            artifact["container_id"] = container_id

        if hasattr(self, "save_artifacts"):
            self.save_artifacts(artifacts)
        else:
            for artifact in artifacts:
                self.save_artifact(artifact)

    def _seek(self, consumer, tp_list):
        config = self.get_config()
        topic = config["topic"]

        if self._state.get(topic) is None:
            if config.get("read_from_beginning"):
                consumer.seek_to_beginning()
            self._state[topic] = {}
        else:
            for tp in tp_list:
                offset = self._state[topic].get(str(tp.partition), 0)
                consumer.seek(tp, offset)

    def _on_poll(self, param):
        self.debug_print("param", param)

        config = self.get_config()

        # Add an action result to the App Run
        action_result = self.add_action_result(phantom.ActionResult(dict(param)))

        if int(param.get("container_count", 0)) <= 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAKFA_ERROR_CONTAINER_COUNT)

        if self.is_poll_now() and int(param.get("artifact_count", 0)) <= 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAKFA_ERROR_ARTIFACT_COUNT)

        topic = config.get("topic")

        if bool(re.compile(r"[^A-Za-z0-9._-]").search(topic)):
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TOPIC_INVALID_ERROR)

        consumer = KafkaConsumer(**self._client_args)

        partitions = consumer.partitions_for_topic(topic)
        if not partitions:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TOPIC_NOT_FOUND)

        tp_list = []
        for partition in partitions:
            tp_list.append(TopicPartition(topic, partition))

        consumer.assign(tp_list)

        if self.is_poll_now():
            consumer.seek_to_beginning()
            max_messages = int(param.get("artifact_count", 0))
            poll_dict = consumer.poll(timeout_ms=int(config.get("timeout", 0)), max_records=max_messages)

        else:
            max_messages = self._seek(consumer, tp_list)
            poll_dict = consumer.poll(timeout_ms=int(config.get("timeout", 0)))

        messages = []
        for tp in tp_list:
            messages += poll_dict.get(tp, [])

        if not self.is_poll_now():
            for tp in tp_list:
                self._state[topic][str(tp.partition)] = consumer.position(tp)

        if not messages:
            return action_result.set_status(phantom.APP_SUCCESS, consts.KAFKA_NO_MESSAGES)

        parser = config.get("message_parser")
        parser_args = []

        for message in messages:
            message_dict = {}
            message_dict["partition"] = message.partition
            message_dict["offset"] = message.offset
            message_dict["message"] = message.value.decode("utf-8")
            parser_args.append(message_dict)

        if parser:
            parser_name = config["message_parser__filename"]
            self.save_progress(consts.KAFKA_USING_PARSER.format(parser_name))

            message_parser = imp.new_module(KAFKA_PARSER_MODULE_NAME)

            try:
                exec(parser in message_parser.__dict__)
                containers = message_parser.parse_messages(topic, parser_args)
            except Exception as e:
                return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_MESSAGE_PARSER.format(parser_name, e))

        else:
            containers = parse_messages(topic, parser_args)

        for container in containers:
            self._save_container(container)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _post_data(self, param):
        self.debug_print("param", param)

        # Add an action result to the App Run
        action_result = self.add_action_result(phantom.ActionResult(dict(param)))

        timeout = int(param.get("timeout", 0))

        if timeout < 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_BAD_TIMEOUT)

        topic = param.get("topic")

        if bool(re.compile(r"[^A-Za-z0-9._-]").search(topic)):
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TOPIC_INVALID_ERROR)

        data_type = param.get("data_type")
        data = param.get("data")

        if data_type == "JSON":
            self._producer.config["value_serializer"] = lambda x: json.dumps(x, indent=4, separators=(",", ": "), ensure_ascii=False).encode(
                "utf-8"
            )

            try:
                data = json.loads(data)
            except json.scanner.JSONDecodeError as e:
                return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_BAD_JSON.format(e))

        elif data_type == "string":
            pass

        else:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_DATA_TYPE.format(data_type))

        if not isinstance(data, list):
            data = [data]

        if len(data) == 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_EMPTY_LIST)

        count = 0
        failed = 0
        for message in data:
            count += 1

            try:
                if data_type == "string":
                    message = bytes(message, encoding="utf8")

                send = self._producer.send(topic, message)

                if timeout:
                    send_data = send.get(timeout=timeout)

                    if send_data.partition is None:
                        raise Exception(consts.KAFKA_ERROR_NO_PARTITION)
                    if send_data.offset is None:
                        raise Exception(consts.KAFKA_ERROR_NO_OFFSET)

                    action_result.add_data(self._build_result_dict(send_data))

                elif count == len(data):
                    send.get()

            except KafkaTimeoutError:
                self.save_progress(consts.KAFKA_ERROR_TIMEOUT)
                action_result.add_data({"message": message, "topic": topic, "status": "failed", "error": consts.KAFKA_ERROR_TIMEOUT})
                failed += 1

            except Exception as e:
                self.save_progress(consts.KAFKA_PRODUCER_SEND_ERROR.format(e))
                action_result.add_data({"message": message, "topic": topic, "status": "failed", "error": str(e)})
                failed += 1

        if failed:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_SEND_FAILED.format(failed, "" if failed == 1 else "s"))

        return action_result.set_status(phantom.APP_SUCCESS, consts.KAFKA_SUCCESS_SEND)

    def _check_hosts(self, hosts):
        failed = False

        for host in hosts:
            try:
                split_host = host.split(":")

                if len(split_host) == 2:
                    if int(split_host[1]) < 0:
                        self.save_progress(consts.KAFKA_ERROR_INVALID_PORT.format(host, split_host[1]))
                        failed = True

                KafkaProducer(**self._client_args)

            except NoBrokersAvailable as e:
                self.save_progress(consts.KAFKA_PRODUCER_NO_BROKERS_ERROR.format(host, e))
                failed = True

            except ValueError:
                self.save_progress(consts.KAFKA_ERROR_INVALID_PORT.format(host, host.split(":")[1]))
                failed = True

            except Exception as e:
                self.save_progress(consts.KAFKA_ERROR_CONNECTIVITY_FAILED.format(host, e))
                failed = True

        return not failed

    def _build_result_dict(self, data):
        result_dict = {}
        result_dict["partition"] = data.partition
        result_dict["offset"] = data.offset
        result_dict["timestamp"] = data.timestamp
        result_dict["topic"] = data.topic
        result_dict["checksum"] = data.checksum
        result_dict["serialized_key_size"] = data.serialized_key_size
        result_dict["serialized_value_size"] = data.serialized_value_size
        result_dict["topic_partition"] = data.topic_partition.partition

        return result_dict

    def handle_action(self, param):
        ret_val = None

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == self.ACTION_ID_TEST_CONNECTIVITY:
            ret_val = self._test_connectivity(param)
        if action_id == self.ACTION_ID_POST_DATA:
            ret_val = self._post_data(param)
        if action_id == self.ACTION_ID_ON_POLL:
            ret_val = self._on_poll(param)

        return ret_val


if __name__ == "__main__":
    import argparse
    import sys

    import pudb
    import requests

    pudb.set_trace()

    argparser = argparse.ArgumentParser()

    argparser.add_argument("input_test_json", help="Input Test JSON file")
    argparser.add_argument("-u", "--username", help="username", required=False)
    argparser.add_argument("-p", "--password", help="password", required=False)
    argparser.add_argument("-v", "--verify", action="store_true", help="verify", required=False, default=False)

    args = argparser.parse_args()
    session_id = None

    if args.username and args.password:
        login_url = phantom.BaseConnector._get_phantom_base_url() + "login"
        try:
            print("Accessing the Login page")
            r = requests.get(login_url, verify=args.verify, timeout=consts.DEFAULT_TIMEOUT)
            csrftoken = r.cookies["csrftoken"]
            data = {"username": args.username, "password": args.password, "csrfmiddlewaretoken": csrftoken}
            headers = {"Cookie": f"csrftoken={csrftoken}", "Referer": login_url}

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=args.verify, data=data, headers=headers, timeout=consts.DEFAULT_TIMEOUT)
            session_id = r2.cookies["sessionid"]

        except Exception as e:
            print(f"Unable to get session id from the platform. Error: {e!s}")
            sys.exit(1)

    if len(sys.argv) < 2:
        print("No test json specified as input")
        sys.exit(0)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = KafkaConnector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json["user_session_token"] = session_id

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    sys.exit(0)
