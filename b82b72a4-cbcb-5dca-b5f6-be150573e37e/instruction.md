# boto3 client spans follow botocore's requests instead of the client call

The repository at `/app/sentry-python` is the Sentry Python SDK, installed in editable mode with its dependencies, including boto3 and botocore 1.43.105. There is no network access.

With the boto3 integration enabled, the span the SDK records for an AWS client call (named `aws.<service>.<Operation>`, for example `aws.s3.GetObject`, with op `http.client`) starts when botocore creates an HTTP request and ends when botocore reports the result. That does not match one client call:

- botocore creates a fresh request for every retry attempt, so a retried call records one client span per attempt.
- A call that fails before botocore creates any request, for example because an event handler raises while the parameters are being built, records no span at all.
- For a response whose body is a `StreamingBody`, the client span ends as soon as the call returns, before the body has been read, so the span for reading the body outlives the call it belongs to.

Make the boto3 integration record exactly one client span per client method call, in the static tracing mode and with span streaming (`trace_lifecycle="stream"`) alike:

- The client span covers the whole call, including every retry attempt. Each request botocore creates for the call carries that same span in its request context, under the `_sentrysdk_span` key the integration already uses.
- When the call raises, including after its retries are exhausted, the caller receives exactly the exception botocore raised, the same object, and the client span finishes once with an error status.
- When the response holds a `StreamingBody`, the client span stays open after the call returns and finishes once the body is consumed: read to the end, read up to its content length, closed, or left as a context manager. The span for reading the body (op `http.client.stream`, same name) is a child of the client span and finishes before it. If reading the body raises, the caller receives that exception and both spans finish with an error status. A response without a streaming body finishes its client span when the call returns.
- While the call runs, the client span is the current span, so the HTTP span the stdlib integration records for the request is its child. As soon as the call returns, the caller's current span is current again, even while the body is still open, and spans started afterwards are never children of the client span or the stream span.
- Breadcrumbs, the HTTP request data recorded on the span, and trace propagation headers are still recorded for each request as they are now.

Fix this in the library source under `/app/sentry-python/sentry_sdk`, keeping every other behaviour of the SDK unchanged. Only your changes under `/app/sentry-python/sentry_sdk` are kept; changes elsewhere in the repository, including to its configuration, are discarded.
