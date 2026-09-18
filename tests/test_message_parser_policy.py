# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_manifest_requires_edit_code_for_custom_message_parser():
    manifest = json.loads((ROOT / "kafka.json").read_text())

    assert manifest["configuration"]["message_parser"]["data_type"] == "python_script"
    assert manifest["min_phantom_version"] == "8.9.0"


def test_connector_executes_the_permission_gated_parser():
    source = (ROOT / "kafka_connector.py").read_text()

    assert 'config.get("message_parser")' in source
    assert "exec(parser, message_parser.__dict__)" in source
