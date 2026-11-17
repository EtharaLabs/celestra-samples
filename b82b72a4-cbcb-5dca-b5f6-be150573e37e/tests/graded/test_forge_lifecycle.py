from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import boto3
import pytest
from botocore.awsrequest import AWSResponse
from botocore.config import Config

import sentry_sdk
from sentry_sdk import capture_message
from sentry_sdk.consts import OP
from sentry_sdk.integrations.boto3 import Boto3Integration
from sentry_sdk.integrations.boto3.consts import ORIGIN
from tests.integrations.boto3.aws_mock import Body

session = boto3.Session(  # type: ignore[attr-defined]
    aws_access_key_id="-",
    aws_secret_access_key="-",
    region_name="eu-north-1",
)


def _serve(payload):
    class S3Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), S3Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def two_byte_s3_server():
    yield from _serve(b"xy")


@pytest.fixture
def two_line_s3_server():
    yield from _serve(b"x\ny\n")


def _init(sentry_init, span_streaming, **options):
    sentry_init(
        traces_sample_rate=1.0,
        trace_lifecycle="stream" if span_streaming else "static",
        integrations=[Boto3Integration()],
        default_integrations=False,
        server_name="",
        **options,
    )


def _parent(span_streaming):
    if span_streaming:
        return sentry_sdk.traces.start_span(name="parent")  # type: ignore[attr-defined]
    return sentry_sdk.start_transaction(name="parent")


def _finished(span, span_streaming):
    return (span.end_timestamp if span_streaming else span.timestamp) is not None


def _s3_client(server):
    return session.client(
        "s3",
        endpoint_url="http://127.0.0.1:%s" % server.server_port,
        config=Config(
            retries={"total_max_attempts": 1, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )


def _record_client_spans(client):
    request_client_spans = []

    def record_client_span(request, **kwargs):
        request_client_spans.append(request.context["_sentrysdk_span"])

    client.meta.events.register("request-created", record_client_span)
    return request_client_spans


def _client_spans(items, span_streaming):
    if span_streaming:
        spans = [item.payload for item in items if item.type == "span"]
        return [
            span
            for span in spans
            if span["attributes"].get("sentry.origin") == ORIGIN
            and span["attributes"].get("sentry.op") == OP.HTTP_CLIENT
        ]
    transaction = next(item.payload for item in items if item.type == "transaction")
    return [
        span
        for span in transaction["spans"]
        if span["origin"] == ORIGIN and span["op"] == OP.HTTP_CLIENT
    ]


@pytest.mark.parametrize("span_streaming", [True, False])
def test_partial_read_keeps_client_span_open(
    sentry_init, two_byte_s3_server, span_streaming
):
    _init(sentry_init, span_streaming)
    client = session.client(
        "s3",
        endpoint_url="http://127.0.0.1:%s" % two_byte_s3_server.server_port,
        config=Config(
            retries={"total_max_attempts": 1, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )
    request_client_spans = []

    def record_client_span(request, **kwargs):
        request_client_spans.append(request.context["_sentrysdk_span"])

    client.meta.events.register("request-created", record_client_span)

    with _parent(span_streaming):
        body = client.get_object(Bucket="bucket", Key="key")["Body"]
        (span,) = request_client_spans

        # one of two bytes read: the body is not consumed yet.
        assert body.read(1) == b"x"
        assert not _finished(span, span_streaming)

        # the content length is now reached.
        assert body.read(1) == b"y"
        assert _finished(span, span_streaming)


@pytest.mark.parametrize("span_streaming", [True, False])
def test_each_retry_attempt_records_a_breadcrumb(
    sentry_init, capture_events, monkeypatch, span_streaming
):
    _init(sentry_init, span_streaming)
    monkeypatch.setattr("botocore.endpoint.time.sleep", lambda delay: None)
    client = session.client(
        "s3", config=Config(retries={"total_max_attempts": 3, "mode": "standard"})
    )
    status_codes = [500, 500, 200]
    attempts = []

    def respond(request, **kwargs):
        attempts.append(request)
        return AWSResponse(request.url, status_codes[len(attempts) - 1], {}, Body(b""))

    client.meta.events.register("before-send", respond)
    events = capture_events()

    with _parent(span_streaming):
        client.head_object(Bucket="bucket", Key="foo")
    capture_message("after the call")

    assert len(attempts) == 3
    event = next(event for event in events if event.get("message") == "after the call")
    crumbs = [
        crumb
        for crumb in event["breadcrumbs"]["values"]
        if crumb["type"] == "http" and crumb["category"] == "httplib"
    ]
    assert len(crumbs) == 3


@pytest.mark.parametrize("span_streaming", [True, False])
def test_propagation_header_names_the_recorded_client_span(
    sentry_init, capture_items, span_streaming
):
    _init(sentry_init, span_streaming)
    client = session.client(
        "s3", config=Config(retries={"total_max_attempts": 1, "mode": "standard"})
    )
    sent = []

    def respond(request, **kwargs):
        header = request.headers.get("sentry-trace")
        sent.append(header.decode() if isinstance(header, bytes) else header)
        return AWSResponse(request.url, 200, {}, Body(b""))

    client.meta.events.register("before-send", respond)
    items = capture_items()

    with _parent(span_streaming):
        client.head_object(Bucket="bucket", Key="foo")
    sentry_sdk.flush()

    (header,) = sent
    assert header is not None
    (client_span,) = _client_spans(items, span_streaming)
    trace_id, span_id = header.split("-")[:2]
    assert span_id == client_span["span_id"]
    assert trace_id == client_span["trace_id"]


@pytest.mark.parametrize("span_streaming", [True, False])
def test_readlines_consumes_the_body(sentry_init, two_line_s3_server, span_streaming):
    _init(sentry_init, span_streaming)
    client = _s3_client(two_line_s3_server)
    request_client_spans = _record_client_spans(client)

    with _parent(span_streaming):
        body = client.get_object(Bucket="bucket", Key="key")["Body"]
        (span,) = request_client_spans
        assert not _finished(span, span_streaming)

        # readlines() reads the body to the end.
        assert body.readlines() == [b"x\n", b"y\n"]
        assert _finished(span, span_streaming)


@pytest.mark.parametrize("span_streaming", [True, False])
def test_readinto_to_the_end_consumes_the_body(
    sentry_init, two_byte_s3_server, span_streaming
):
    _init(sentry_init, span_streaming)
    client = _s3_client(two_byte_s3_server)
    request_client_spans = _record_client_spans(client)

    with _parent(span_streaming):
        body = client.get_object(Bucket="bucket", Key="key")["Body"]
        (span,) = request_client_spans

        buffer = bytearray(1)
        assert body.readinto(buffer) == 1
        assert not _finished(span, span_streaming)

        received = bytes(buffer)
        while body.readinto(buffer):
            received += bytes(buffer)
        assert received == b"xy"
        assert _finished(span, span_streaming)


@pytest.mark.parametrize("span_streaming", [True, False])
def test_streaming_payload_keeps_client_span_open(sentry_init, span_streaming):
    _init(sentry_init, span_streaming)
    client = session.client("lambda")
    request_client_spans = _record_client_spans(client)

    def respond(request, **kwargs):
        return AWSResponse(request.url, 200, {"content-length": "1"}, Body(b"x"))

    client.meta.events.register("before-send", respond)

    with _parent(span_streaming) as parent:
        payload = client.invoke(FunctionName="function")["Payload"]
        (span,) = request_client_spans

        # Lambda returns its StreamingBody under Payload rather than Body.
        assert not _finished(span, span_streaming)
        if span_streaming:
            assert sentry_sdk.traces.get_current_span() is parent  # type: ignore[attr-defined]
        else:
            assert sentry_sdk.get_current_span() is parent

        assert payload.read() == b"x"
        assert _finished(span, span_streaming)
