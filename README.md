[comment]: # "Auto-generated SOAR connector documentation"
# Kafka

Publisher: Splunk  
Connector Version: 2.0.7  
Product Vendor: Apache  
Product Name: Kafka  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.1  

This app implements ingesting and sending data on the Apache Kafka messaging system

[comment]: # " File: README.md"
[comment]: # "  Copyright (c) 2017-2023 Splunk Inc."
[comment]: # ""
[comment]: # "Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "you may not use this file except in compliance with the License."
[comment]: # "You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "    http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "either express or implied. See the License for the specific language governing permissions"
[comment]: # "and limitations under the License."
[comment]: # ""
## Kerberos Authentication

If you wish to authenticate with the Kafka instance using Kerberos, the following items are needed:

-   A Kerberos Principal will be needed for " **phantom** "
-   Normal Kerberos requirements (KDC, Keytabs, Principals, etc) still apply
-   **kinit** must be run for the **phantom** principal, for the **phantom-worker** user
-   It should be noted that Kerberos tickets will expire, so it is recommended to use a script to
    run **kinit** periodically to refresh the ticket for **phantom-worker**

## SSL Authentication

To authenticate with the Kafka instance using SSL, the following configuration parameters may be
required. They are to be pointed to the location of certain files:

-   **cert_file** - A signed certificate file that is trusted by the Kafka instance
-   **key_file** - The key used to generate **cert_file**
-   **ca_cert** - The certificate of the certificate authority that signed **cert_file**

It is recommended that these files be placed under the **\<PHANTOM_HOME>/etc/ssl/** directory. These
files must be readable by the **phantom-worker** user.  
  
Note that not all of these files will be necessary for all setups. More than likely, **cert_file**
will be required. However, the other parameters will be needed in certain cases. For example,
**ca_cert** will be needed if you set up your own certificate authority.

## GSSAPI

The Kerberos authentication for this app uses the python-gssapi module, which is licensed under the
ISC License, Copyright (c) 2014, The Python GSSAPI Team.


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Kafka asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**hosts** |  required  | string | Hosts in the cluster (comma separated e.g. host1.com:9092,host2.org:2181,10.10.10.10:9092)
**topic** |  required  | string | Topic to subscribe to for ingestion
**message_parser** |  optional  | file | Python file containing a message parsing method
**timeout** |  required  | numeric | How long to poll for messages each interval (ms)
**read_from_beginning** |  required  | boolean | Start ingesting from the beginning of the topic
**use_kerberos** |  optional  | boolean | Use Kerberos auth
**use_ssl** |  optional  | boolean | Use SSL
**cert_file** |  optional  | string | Path to SSL certificate file
**key_file** |  optional  | string | Path to SSL key file
**ca_cert** |  optional  | string | Path to CA certificate file

### Supported Actions  
[test connectivity](#action-test-connectivity) - Checks connectivity with configured hosts  
[on poll](#action-on-poll) - Ingest messages from Kafka  
[post data](#action-post-data) - Post data to a Kafka topic  

## action: 'test connectivity'
Checks connectivity with configured hosts

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'on poll'
Ingest messages from Kafka

Type: **ingest**  
Read only: **False**

Basic configuration parameters for this action are available in asset configuration.<br><br>If <b>read_from_beginning</b> is set to true, the first poll will begin reading messages from the start of a topic, ingesting as many messages as can be ingested within the time set by the <b>timeout</b> asset configuration parameter. For a <b>poll now</b>, the app will ingest as many messages as specified by <b>artifact_count</b>, starting at the beginning of the topic.<br><br>This app creates containers and artifacts using the same format as the REST endpoint. It uses a message parsing method to decide how the containers and artifacts will look. A custom message parsing script can be uploaded during asset configuration to change how Kafka messages are ingested as containers and artifacts. There are three requirements for this script:<ul><li>It must contain a method called <b>parse_messages</b>. This is the method that will be called during the poll.</li><li>The method must accept exactly two arguments:<ul><li>First argument: A string which will be the name of the topic.</li><li>Second argument: A list of dictionaries, with a dictionary containing data for each ingested message. Each dictionary will have 3 fields: <b>message</b>, <b>offset</b>, and <b>partition</b>.</li></ul><li>The method must return a list of dictionaries. Each dictionary must contain two fields:</li><ul><li><b>container</b> - a dictionary formatted as the body of a REST call to the Phantom /rest/container endpoint.</li><li><b>artifacts</b> - a list of dictionaries, with each dictionary formatted as the body of a REST call to the Phantom /rest/artifact endpoint.</li></ul></ul>Refer to the <b>REST API Documentation</b> section of the Phantom docs for more information on what can be included in the dictionaries used to create the containers and artifacts during ingestion.<br><br>The default message parsing script is called <b>kafka_parser.py</b> and can be found in the Kafka app directory. It contains:<br><br><pre>from datetime import datetime<br>time_format = '%Y-%m-%d %H:%M:%S'<br><br><br>def parse_messages(topic, messages):<br><br>    ret_json = {}<br>    container_json = {}<br>    artifact_list = []<br><br>    ret_json['container'] = container_json<br>    ret_json['artifacts'] = artifact_list<br><br>    name = 'Messages ingested from {0} at {1}'.format(topic, datetime.now().strftime(time_format))<br><br>    container_json['name'] = name<br>    container_json['description'] = 'Some messages from Kafka'<br>    container_json['run_automation'] = False<br><br>    count = 0 <br>    num_artifacts = len(messages)<br>    for message in messages:<br><br>        artifact_json = {}<br>        artifact_list.append(artifact_json)<br><br>        artifact_json['source_data_identifier'] = '{0}:{1}'.format(message['partition'], message['offset'])<br>        artifact_json['cef'] = {'message': message['message']}<br>        artifact_json['name'] = message['message'][:100]<br><br>        if count < num_artifacts - 1:<br>            artifact_json['run_automation'] = False<br><br>        count += 1<br><br>    return [ret_json]</pre><br> This script will create one container per poll, and create one artifact in that container per message ingested. The source data identifier for the artifacts will have the format <code>&lt;partition&gt;:&lt;offset&gt;</code> for each message. The data from the message will be put in the <b>message</b> CEF field. Any formatting of the data will not be preserved. Supply a custom parser to format the data as needed.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**start_time** |  optional  | Parameter ignored in this app | numeric | 
**end_time** |  optional  | Parameter ignored in this app | numeric | 
**container_id** |  optional  | Parameter ignored in this app | string | 
**container_count** |  optional  | Parameter ignored in this app | numeric | 
**artifact_count** |  optional  | Maximum number of messages to ingest during poll now | numeric | 

#### Action Output
No Output  

## action: 'post data'
Post data to a Kafka topic

Type: **generic**  
Read only: **False**

This action creates a short-lived Kafka Producer that will post the supplied data to the given topic, then exit.<br><br>Two types of data are supported right now: string and JSON. When sending JSON, the app will format the JSON before posting it to the Kafka server. If the JSON is a list, the app will send each element of the list in separate messages. To send a list to Kafka, add an extra set of brackets around the list.<br><br>If the <b>timeout</b> parameter is set to 0 (which is the default), the app will not wait for the Kafka server to acknowledge receipt of the message. In such a scenario, the action will not fill the <b>action_result.data.\*</b> data paths in the result.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**data_type** |  required  | The type of the data being posted (can be string or JSON) | string | 
**data** |  required  | The data to post | string | 
**topic** |  required  | The topic to post the data to | string |  `kafka topic` 
**timeout** |  optional  | How long (in seconds) to wait for message to be acknowledged by server | numeric | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |  
action_result.parameter.data | string |  |  
action_result.parameter.data_type | string |  |  
action_result.parameter.timeout | numeric |  |  
action_result.parameter.topic | string |  `kafka topic`  |  
action_result.data.\*.checksum | numeric |  |  
action_result.data.\*.offset | numeric |  |  
action_result.data.\*.partition | numeric |  |  
action_result.data.\*.serialized_key_size | numeric |  |  
action_result.data.\*.serialized_value_size | numeric |  |  
action_result.data.\*.timestamp | numeric |  |  
action_result.data.\*.topic | string |  `kafka topic`  |  
action_result.data.\*.topic_partition | numeric |  |  
action_result.summary | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |  