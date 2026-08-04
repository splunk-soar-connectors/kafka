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
import ast
from pathlib import Path


CONNECTOR_SOURCE = Path(__file__).parents[1] / "kafka_connector.py"


def test_connector_has_no_dynamic_execution_primitive():
    tree = ast.parse(CONNECTOR_SOURCE.read_text())
    called_names = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}

    assert "exec" not in called_names
    assert "eval" not in called_names
    assert "compile" not in called_names


def test_legacy_parser_values_are_rejected_during_initialization():
    source = CONNECTOR_SOURCE.read_text()

    assert 'config.get("message_parser")' in source
    assert "Custom message parsers are no longer supported" in source
