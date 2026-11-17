# syntax=docker/dockerfile:1.17@sha256:38387523653efa0039f8e1c89bb74a30504e76ee9f565e25c9a09841f9427b05
FROM --platform=$BUILDPLATFORM alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26 AS source-langgraph
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/langchain-ai/langgraph
ARG COMMIT=230927fb3a9ac9b2893a30322b4dfea7cdea9a8f
# The base commit's committer time, so a plain docker build (as Harbor runs it) dates the
# layers it writes the same way a buildx build passing SOURCE_DATE_EPOCH does.
ARG SOURCE_DATE_EPOCH=1789415119
RUN test -n "$SOURCE_DATE_EPOCH" \
 && git init -q /src \
 && git -C /src fetch -q --depth 1 "$REPO_URL" "$COMMIT" \
 && git -C /src checkout -q FETCH_HEAD \
 && test "$(git -C /src rev-parse HEAD)" = "$COMMIT" \
 && rm -rf /src/.git \
 && git -C /src init -q \
 && git -C /src add -A \
 && GIT_AUTHOR_DATE="@$SOURCE_DATE_EPOCH" GIT_COMMITTER_DATE="@$SOURCE_DATE_EPOCH" \
    git -C /src -c user.name=task -c user.email=task@localhost commit -qm "base" \
 && rm /src/.git/index \
 && git -C /src read-tree HEAD

FROM --platform=$BUILDPLATFORM alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26 AS source-langchain
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/langchain-ai/langchain
ARG COMMIT=f295bfef22e9aeb02ad0f79b49883f4b446e4641
# The base commit's committer time, so a plain docker build (as Harbor runs it) dates the
# layers it writes the same way a buildx build passing SOURCE_DATE_EPOCH does.
ARG SOURCE_DATE_EPOCH=1791989628
RUN test -n "$SOURCE_DATE_EPOCH" \
 && git init -q /src \
 && git -C /src fetch -q --depth 1 "$REPO_URL" "$COMMIT" \
 && git -C /src checkout -q FETCH_HEAD \
 && test "$(git -C /src rev-parse HEAD)" = "$COMMIT" \
 && rm -rf /src/.git \
 && git -C /src init -q \
 && git -C /src add -A \
 && GIT_AUTHOR_DATE="@$SOURCE_DATE_EPOCH" GIT_COMMITTER_DATE="@$SOURCE_DATE_EPOCH" \
    git -C /src -c user.name=task -c user.email=task@localhost commit -qm "base" \
 && rm /src/.git/index \
 && git -C /src read-tree HEAD

FROM --platform=$BUILDPLATFORM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS wheels
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG TARGETOS
ARG TARGETARCH
COPY requirements-tools.txt binary.txt requirements-sdist.txt /req/
RUN case "$TARGETARCH" in amd64) arch=x86_64 ;; arm64) arch=aarch64 ;; *) exit 1 ;; esac \
 && test "$TARGETOS" = linux \
 && pip download --no-cache-dir --require-hashes --only-binary=:all: --no-deps \
      --python-version 3.12 --implementation cp --abi cp312 --abi abi3 --abi none \
      --platform "manylinux_2_28_$arch" --platform "manylinux_2_17_$arch" \
      --platform "manylinux2014_$arch" --platform any \
      -r /req/binary.txt -d /dist \
 && if [ -s /req/requirements-sdist.txt ]; then \
      pip install --no-cache-dir --require-hashes --no-deps -r /req/requirements-tools.txt \
      && pip download --no-cache-dir --require-hashes --no-binary=:all: --no-deps --no-build-isolation -r /req/requirements-sdist.txt -d /dist; \
    fi

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS runtime
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# In the build environment only: pip then writes hash-checked .pyc files and chage pins the
# account's password-change day, so the layers do not depend on the build date.
ARG SOURCE_DATE_EPOCH=1791989628
# Docker Desktop's Rosetta emulation leaves /root/.cache/rosetta behind every root RUN, so
# each one removes it; a QEMU or native build never writes it.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 
# Without network, litellm (imported by rewardkit) retries its cost-map fetch in a thread whose
# logging races the main import and intermittently crashes rewardkit; use the bundled map.
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
RUN groupadd -g 10001 grader && useradd -u 10001 -g 10001 -m -d /home/grader grader \
 && chage -d "$(date -u -d "@$SOURCE_DATE_EPOCH" +%F)" grader \
 && rm -rf /root/.cache
COPY requirements-tools.txt requirements.txt /tmp/req/
RUN --mount=type=bind,from=wheels,source=/dist,target=/dist \
    pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-deps -r /tmp/req/requirements-tools.txt \
 && pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-deps --no-build-isolation -r /tmp/req/requirements.txt \
 && rm -r /tmp/req \
 && rm -rf /root/.cache
COPY --from=source-langgraph /src /grading/langgraph
RUN pip install --no-cache-dir --no-deps --no-build-isolation --no-index -e /grading/langgraph/libs/checkpoint -e /grading/langgraph/libs/checkpoint-sqlite -e /grading/langgraph/libs/checkpoint-postgres -e /grading/langgraph/libs/sdk-py -e /grading/langgraph/libs/prebuilt -e /grading/langgraph/libs/langgraph \
 && rm -rf /root/.cache
COPY --from=source-langchain /src /grading/langchain
RUN pip install --no-cache-dir --no-deps --no-build-isolation --no-index -e /grading/langchain/libs/core -e /grading/langchain/libs/langchain_v1 \
 && rm -rf /root/.cache
COPY graded/ /tests/graded/
# The glob also carries a wrapper's moved original (.trinity-bundle-test.sh), because Harbor
# runs a verifier built from tests/Dockerfile as bundled and never uploads tests/ into it.
COPY judge/ /tests/judge/
COPY *.sh run_graded.py score.py vguard.py reward.toml test_output.py judge.toml reference.diff combine.py /tests/
RUN chmod 0755 /tests/*.sh \
 && mkdir -p /logs/verifier \
 && chown -R 10001:10001 /grading/langgraph /grading/langchain /logs \
 && rm -rf /root/.cache
WORKDIR /grading
USER 10001:10001
LABEL org.opencontainers.image.source="https://github.com/langchain-ai/langgraph, https://github.com/langchain-ai/langchain" \
      org.opencontainers.image.revision="230927fb3a9ac9b2893a30322b4dfea7cdea9a8f, f295bfef22e9aeb02ad0f79b49883f4b446e4641" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.digest="sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
CMD ["/tests/test.sh"]
