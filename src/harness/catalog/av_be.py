"""Service definition for the AV backend Kafka consumer."""

from harness.catalog.service import ServiceDefinition

AvBe = ServiceDefinition(
    name="av-be",
    default_image="av-be:latest",
    aliases=["av-be"],
    exposed_ports=["9000/tcp"],
    health_path="/",
    env={
        # AV eagerly initializes JPA even though zone consumers only use Redis.
        "DB_URI": "jdbc:mariadb://mysql:3306/av",
        "DB_USER": "root",
        "DB_PASSWORD": "root",
        "NV_REDIS_COMMON_ENABLE": "true",
        "NV_REDIS_HOST": "redis-av:6379",
        "NV_REDIS_PASSWORD": "",
        "NV_KAFKA_SERVERS": "kafka:9092",
        "NV_KAFKA_AUTH_BROKERS": "kafka:9092",
        "NV_KAFKA_GROUP_ID": "integration-av-zone-consumer",
        "NV_KAFKA_STREAMS_ENABLE_CONSUMER": "true",
        "NV_KAFKA_STREAMS_ENABLE_PRODUCER": "false",
        "NV_KAFKA_STREAMS_APPLICATION_ID_CONFIG": "integration-av-zone",
        "NV_KAFKA_STREAMS_AUTO_OFFSET_RESET_CONFIG": "earliest",
        "NV_KAFKA_STREAMS_NUM_STREAM_THREADS_CONFIG": "1",
        "NV_KAFKA_ZONES_PROTO_TOPIC": "it-av-lm-zones",
        "NV_KAFKA_ZONES_FIRST_MILE_ZONE_EVENT_TOPIC": "it-av-fm-zones",
        # AV constructs all of these consumer sources during bootstrap.
        "NV_KAFKA_ORDER_EVENTS_PROTO_TOPIC": "it-av-order-events",
        "NV_KAFKA_ORDER_CREATE_EVENT_TOPIC": "it-av-order-create",
        "NV_KAFKA_AV_VERIFICATION_RESPONSE_TOPIC": "it-av-verification-response",
        "NV_KAFKA_ADDRESSES_PROTO_TOPIC": "it-av-addresses",
        "NV_KAFKA_MAXWELL_TOPIC": "it-av-maxwell",
        "NV_KAFKA_AV_VERIFICATION_PROTO_TOPIC": "it-av-verification",
        "NV_KAFKA_AV_VERIFICATION_REQUEST_TOPIC": "it-av-verification-request",
        "NV_AUTH_SERVICE_ID": "AV",
        "NV_AUTH_SERVICE_SECRET": "test-secret",
        "NV_AUTH_API_URL": "http://mock-services:8080/global/aaa",
        "NV_ES_ADDRESS_VERIFICATION_CLUSTER_NODES": "localhost",
        "NV_ES_ADDRESS_VERIFICATION_CLUSTER_PORT": "9200",
        "NV_FEATURE_HUB_EDGE_URL": "http://localhost:1",
        "NV_FEATURE_HUB_CLIENT_EVAL_KEY": "integration-test",
    },
    startup_timeout=180.0,
)
