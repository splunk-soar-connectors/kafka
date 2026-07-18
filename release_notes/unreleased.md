**Unreleased**
Require TLS hostname verification when Kafka assets use a custom CA certificate (PSAAS-31301).
Persist Kafka poll offsets only after decoded messages and their containers and artifacts are saved successfully (PSAAS-32240).
Resolve every Kafka producer send future so broker rejections for intermediate batch messages fail the action (PSAAS-32365).
