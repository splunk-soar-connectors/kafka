# --
# File: kafka_connector.py
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

# Phantom App imports
import phantom.app as phantom

# Imports local to this App
import kafka_consts as consts
from kafka_parser import parse_messages

import os
import re
import imp
import inspect
import simplejson as json

app_dir = os.path.dirname(os.path.abspath(__file__))  # noqa
if (os.path.exists('{}/dependencies'.format(app_dir))):  # noqa
    os.sys.path.insert(0, '{}/dependencies/kafka-python'.format(app_dir))  # noqa
    os.sys.path.insert(0, '{}/dependencies'.format(app_dir))  # noqa
from kafka import KafkaProducer, KafkaConsumer, TopicPartition  # pylint: disable=E0611
from kafka.errors import KafkaTimeoutError, NoBrokersAvailable  # pylint: disable=E0401,E0611

KAFKA_PARSER_MODULE_NAME = "custom_parser"


# Define the App Class
class KafkaConnector(phantom.BaseConnector):

    ACTION_ID_TEST_CONNECTIVITY = "test_connectivity"
    ACTION_ID_POST_DATA = "post_data"
    ACTION_ID_ON_POLL = "on_poll"

    def __init__(self):

        # Call the BaseConnectors init first
        super(KafkaConnector, self).__init__()

        self._state = {}
        self.producer = None

    def initialize(self):

        if (hasattr(self, 'load_state')):
            self._state = self.load_state()
        else:
            self._load_state()

        try:

            if self.get_action_identifier() == self.ACTION_ID_POST_DATA:
                host_list = self.get_config()['hosts'].split(',')
                self.producer = KafkaProducer(bootstrap_servers=host_list)

        except Exception as e:
            return self.set_status(phantom.APP_ERROR, consts.KAFKA_PRODUCER_CREATE_ERROR.format(e))

        return phantom.APP_SUCCESS

    def finalize(self):

        if (hasattr(self, 'save_state')):
            self.save_state(self._state)
        else:
            self._save_state()

        return phantom.APP_SUCCESS

    def _load_state(self):

        dirpath = os.path.split(os.path.abspath(__file__))[0]
        asset_id = self.get_asset_id()
        state_file_path = "{0}/{1}_state.json".format(dirpath, asset_id)

        self._state = {}

        try:
            with open(state_file_path, 'r') as f:
                in_json = f.read()
                self._state = json.loads(in_json)
        except Exception as e:
            self.debug_print("In _load_state: Exception: {0}".format(str(e)))
            pass

        self.debug_print("Loaded state: ", self._state)

        return phantom.APP_SUCCESS

    def _save_state(self):

        self.debug_print("Saving state: ", self._state)

        dirpath = os.path.split(os.path.abspath(__file__))[0]
        asset_id = self.get_asset_id()
        state_file_path = "{0}/{1}_state.json".format(dirpath, asset_id)

        if (not state_file_path):
            self.debug_print("_state_file_path is None in _save_state")
            return phantom.APP_SUCCESS

        try:
            with open(state_file_path, 'w+') as f:
                f.write(json.dumps(self._state))
        except:
            pass

        return phantom.APP_SUCCESS

    def _test_connectivity(self, param):

        action_result = self.add_action_result(phantom.ActionResult(dict(param)))

        config = self.get_config()

        host_list = config['hosts'].split(',')

        try:
            KafkaProducer(bootstrap_servers=host_list)
        except Exception as e:
            self.save_progress(consts.KAFKA_PRODUCER_CREATE_ERROR.format(e))
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TEST_CONNECTIVITY_FAILED)

        if not self._check_hosts(host_list):
            self.save_progress(consts.KAFKA_WARNING_SOME_HOSTS_FAILED)

        parser = config.get('message_parser')

        if parser:

            parser_name = config['message_parser__filename']

            self.save_progress(consts.KAFKA_TEST_PARSER.format(parser_name))

            message_parser = imp.new_module(KAFKA_PARSER_MODULE_NAME)

            try:

                exec parser in message_parser.__dict__

                num_args = len(inspect.getargspec(message_parser.parse_messages).args)
                if num_args != 2:
                    return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_PARSER_ARGS.format(parser_name, num_args))

                message_parser.parse_messages(config['topic'], consts.KAFKA_TEST_MESSAGES)

            except Exception as e:
                return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_MESSAGE_PARSER.format(parser_name, e))

        self.save_progress(consts.KAFKA_TEST_CONNECTIVITY_PASSED)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _save_container(self, container_dict):

        config = self.get_config()

        container = container_dict.get('container')

        container['label'] = config.get('ingest', {}).get('container_label')

        ret_val, message, container_id = self.save_container(container)

        if (not ret_val):
            return ret_val, message

        artifacts = container_dict.get('artifacts')

        for artifact in artifacts:
            artifact['container_id'] = container_id

        if (hasattr(self, 'save_artifacts')):
            self.save_artifacts(artifacts)
        else:
            for artifact in artifacts:
                self.save_artifact(artifact)

    def _seek(self, param, consumer, tp):

        config = self.get_config()

        if self.is_poll_now():

            self.debug_print('Starting poll now')

            consumer.seek_to_end()
            max_messages = param.get('artifact_count')
            offset = max([0, consumer.position(tp) - max_messages])
            consumer.seek(tp, offset)

            return max_messages

        if (self._state.get('first_run', True)):

            self._state['first_run'] = False

            max_messages = int(config.get('first_run_max_messages'))

            if (config.get('read_from_beginning')):
                consumer.seek_to_beginning()

            else:
                consumer.seek_to_end()
                offset = max([0, consumer.position(tp) - max_messages])
                consumer.seek(tp, offset)

        else:

            max_messages = int(config.get('max_messages'))
            offset = self._state.get('last_offset', consumer.position(tp))
            consumer.seek(tp, offset)

        return max_messages

    def _on_poll(self, param):

        self.debug_print("param", param)

        config = self.get_config()

        # Add an action result to the App Run
        action_result = self.add_action_result(phantom.ActionResult(dict(param)))

        if int(param.get('container_count', 0)) <= 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAKFA_ERROR_CONTAINER_COUNT)

        if self.is_poll_now() and int(param.get('artifact_count', 0)) <= 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAKFA_ERROR_ARTIFACT_COUNT)

        topic = config.get('topic')

        if bool(re.compile(r'[^A-Za-z0-9._-]').search(topic)):
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TOPIC_INVALID_ERROR)

        host_list = self.get_config()['hosts'].split(',')

        if not self._check_hosts(host_list):
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_PRODUCER_CREATE_ERROR)

        consumer = KafkaConsumer(bootstrap_servers=host_list)

        partitions = consumer.partitions_for_topic(topic)
        if (not partitions):
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TOPIC_NOT_FOUND)

        tp = TopicPartition(topic, partitions.pop())

        consumer.assign([tp])

        max_messages = self._seek(param, consumer, tp)

        messages = consumer.poll(timeout_ms=1000, max_records=max_messages).get(tp)

        if not self.is_poll_now():
            self._state['last_offset'] = consumer.position(tp)

        if (not messages):
            return action_result.set_status(phantom.APP_SUCCESS, consts.KAFKA_NO_MESSAGES)

        parser = config.get('message_parser')
        parser_args = dict((message.offset, message.value) for message in messages)

        if parser:

            parser_name = config['message_parser__filename']
            self.save_progress(consts.KAFKA_USING_PARSER.format(parser_name))

            message_parser = imp.new_module(KAFKA_PARSER_MODULE_NAME)

            try:
                exec parser in message_parser.__dict__
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

        timeout = int(param.get('timeout', 0))

        if timeout < 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_BAD_TIMEOUT)

        topic = param.get('topic')

        if bool(re.compile(r'[^A-Za-z0-9._-]').search(topic)):
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_TOPIC_INVALID_ERROR)

        data_type = param.get('data_type')
        data = param.get('data')

        if data_type == 'JSON':

            self.producer.config['value_serializer'] = lambda x: json.dumps(x, indent=4, separators=(',', ': '), ensure_ascii=False).encode('utf-8')

            try:
                data = json.loads(data)
            except json.scanner.JSONDecodeError as e:
                return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_BAD_JSON.format(e))

        elif data_type == 'string':
            pass

        else:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_DATA_TYPE.format(data_type))

        if not isinstance(data, list):
            data = [data]

        if len(data) == 0:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_EMPTY_LIST)

        failed = 0
        for message in data:

            try:

                send = self.producer.send(topic, message)

                if timeout:

                    send_data = send.get(timeout=timeout)

                    if send_data.partition is None:
                        raise Exception(consts.KAFKA_ERROR_NO_PARTITION)
                    if send_data.offset is None:
                        raise Exception(consts.KAFKA_ERROR_NO_OFFSET)

                    action_result.add_data(self._build_result_dict(send_data))

            except KafkaTimeoutError:
                self.save_progress(consts.KAFKA_ERROR_TIMEOUT)
                action_result.add_data({"message": message, "topic": topic, "status": "failed", "error": consts.KAFKA_ERROR_TIMEOUT})
                failed += 1

            except Exception as e:
                self.save_progress(consts.KAFKA_PRODUCER_SEND_ERROR.format(e))
                action_result.add_data({"message": message, "topic": topic, "status": "failed", "error": str(e)})
                failed += 1

        if failed:
            return action_result.set_status(phantom.APP_ERROR, consts.KAFKA_ERROR_SEND_FAILURES.format(failed, '' if failed == 1 else 's'))

        return action_result.set_status(phantom.APP_SUCCESS, consts.KAFKA_SUCCESS_SEND)

    def _check_hosts(self, hosts):

        failed = False

        for host in hosts:

            try:

                split_host = host.split(':')

                if len(split_host) == 2:
                    if int(split_host[1]) < 0:
                        self.save_progress(consts.KAFKA_ERROR_INVALID_PORT.format(host, split_host[1]))
                        failed = True

                KafkaProducer(bootstrap_servers=[host])

            except NoBrokersAvailable as e:
                self.save_progress(consts.KAFKA_PRODUCER_NO_BROKERS_ERROR.format(host, e))
                failed = True

            except ValueError:
                self.save_progress(consts.KAFKA_ERROR_INVALID_PORT.format(host, host.split(':')[1]))
                failed = True

            except Exception as e:
                self.save_progress(consts.KAFKA_ERROR_COULD_NOT_CONNECT.format(host, e))
                failed = True

        return not failed

    def _build_result_dict(self, data):

        result_dict = {}
        result_dict['partition'] = data.partition
        result_dict['offset'] = data.offset
        result_dict['timestamp'] = data.timestamp
        result_dict['topic'] = data.topic
        result_dict['checksum'] = data.checksum
        result_dict['serialized_key_size'] = data.serialized_key_size
        result_dict['serialized_value_size'] = data.serialized_value_size
        result_dict['topic_partition'] = data.topic_partition.partition

        return result_dict

    def handle_action(self, param):

        ret_val = None

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if (action_id == self.ACTION_ID_TEST_CONNECTIVITY):
            ret_val = self._test_connectivity(param)
        if (action_id == self.ACTION_ID_POST_DATA):
            ret_val = self._post_data(param)
        if (action_id == self.ACTION_ID_ON_POLL):
            ret_val = self._on_poll(param)

        return ret_val


if __name__ == '__main__':

    import sys
    # import pudb
    # pudb.set_trace()

    if (len(sys.argv) < 2):
        print "No test json specified as input"
        exit(0)

    with open(sys.argv[1]) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = KafkaConnector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print (json.dumps(json.loads(ret_val), indent=4))

    exit(0)
