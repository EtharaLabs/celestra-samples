# syntax=docker/dockerfile:1.17@sha256:38387523653efa0039f8e1c89bb74a30504e76ee9f565e25c9a09841f9427b05
FROM --platform=$BUILDPLATFORM alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26 AS source
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/getsentry/sentry-python
ARG COMMIT=500f10e79e783754b0dae92119139d2db212602e
# The base commit's committer time, so a plain docker build (as Harbor runs it) dates the
# layers it writes the same way a buildx build passing SOURCE_DATE_EPOCH does.
ARG SOURCE_DATE_EPOCH=1790783392
# The agent's copy carries no version-control history at all, not even a fresh base commit,
# and no submodule remote.
RUN test -n "$SOURCE_DATE_EPOCH" \
 && git init -q /src \
 && git -C /src fetch -q --depth 1 "$REPO_URL" "$COMMIT" \
 && git -C /src checkout -q FETCH_HEAD \
 && test "$(git -C /src rev-parse HEAD)" = "$COMMIT" \
 && rm -rf /src/.git \
 && rm -f /src/.gitmodules

FROM --platform=$BUILDPLATFORM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS wheels
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG TARGETOS
ARG TARGETARCH
COPY requirements-tools.txt binary.txt sdist.txt /req/
# Kaniko leaves TARGETARCH and TARGETOS empty and builds for its own platform, so fall back to that.
RUN case "${TARGETARCH:-$(dpkg --print-architecture)}" in amd64) arch=x86_64 ;; arm64) arch=aarch64 ;; *) exit 1 ;; esac \
 && test "${TARGETOS:-linux}" = linux \
 && pip download --no-cache-dir --require-hashes --only-binary=:all: --no-deps \
      --python-version 3.12 --implementation cp --abi cp312 --abi abi3 --abi none \
      --platform "manylinux_2_28_$arch" --platform "manylinux_2_17_$arch" \
      --platform "manylinux2014_$arch" --platform any \
      -r /req/binary.txt -d /dist \
 && if [ -s /req/sdist.txt ]; then \
      pip install --no-cache-dir --require-hashes --no-deps -r /req/requirements-tools.txt \
      && pip download --no-cache-dir --require-hashes --no-binary=:all: --no-deps --no-build-isolation -r /req/sdist.txt -d /dist; \
    fi

FROM --platform=$BUILDPLATFORM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS agent-wheels
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG TARGETOS
ARG TARGETARCH
COPY agent-tools.txt agent-binary.txt agent-sdist.txt /req/
# Kaniko leaves TARGETARCH and TARGETOS empty and builds for its own platform, so fall back to that.
RUN case "${TARGETARCH:-$(dpkg --print-architecture)}" in amd64) arch=x86_64 ;; arm64) arch=aarch64 ;; *) exit 1 ;; esac \
 && test "${TARGETOS:-linux}" = linux \
 && pip download --no-cache-dir --require-hashes --only-binary=:all: --no-deps \
      --python-version 3.12 --implementation cp --abi cp312 --abi abi3 --abi none \
      --platform "manylinux_2_28_$arch" --platform "manylinux_2_17_$arch" \
      --platform "manylinux2014_$arch" --platform any \
      -r /req/agent-binary.txt -d /dist \
 && if [ -s /req/agent-sdist.txt ]; then \
      pip install --no-cache-dir --require-hashes --no-deps -r /req/agent-tools.txt \
      && pip download --no-cache-dir --require-hashes --no-binary=:all: --no-deps --no-build-isolation -r /req/agent-sdist.txt -d /dist; \
    fi

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS runtime
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# In the build environment only: pip then writes hash-checked .pyc files and chage pins the
# account's password-change day, so the layers do not depend on the build date.
ARG SOURCE_DATE_EPOCH=1790783392
# Docker Desktop's Rosetta emulation leaves /root/.cache/rosetta behind every root RUN, so
# each one removes it; a QEMU or native build never writes it.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 
RUN groupadd -g 10001 agent && useradd -u 10001 -g 10001 -m -d /home/agent agent \
 && chage -d "$(date -u -d "@$SOURCE_DATE_EPOCH" +%F)" agent \
 && rm -rf /root/.cache
COPY requirements-tools.txt requirements.txt /tmp/req/
# Kaniko ignores RUN --mount, so these files are copied in and removed by the step that uses them.
COPY --from=wheels /dist /dist
RUN pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-deps -r /tmp/req/requirements-tools.txt \
 && pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-build-isolation -r /tmp/req/requirements.txt \
 && rm -r /tmp/req \
 && rm -rf /root/.cache /dist
COPY --from=source --chown=10001:10001 /src /app/sentry-python
RUN pip install --no-cache-dir --no-deps --no-build-isolation --no-index -e /app/sentry-python \
 && chown -R 10001:10001 /app/sentry-python \
 && rm -rf /root/.cache
# The agent under test (openhands-sdk==1.58.2) as the benchmark harness runs it: Harbor finds
# /opt/openhands-sdk-venv ready and skips its networked install.
COPY agent-tools.txt agent-requirements.txt /tmp/agent/
# Kaniko ignores RUN --mount, so these files are copied in and removed by the step that uses them.
COPY --from=agent-wheels /dist /agentdist
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261020T213255Z bookworm main\ndeb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261020T213255Z bookworm-updates main\ndeb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261020T213255Z bookworm-security main\n' > /etc/apt/sources.list \
 && rm -f /etc/apt/sources.list.d/debian.sources \
 && apt-get -o Acquire::Check-Valid-Until=false update -qq \
 && apt-get install -y -qq --no-install-recommends curl=7.88.1-10+deb12u15 \
 && rm -rf /var/lib/apt/lists/* /var/log/apt/history.log /var/log/apt/term.log /var/log/dpkg.log /var/cache/ldconfig/aux-cache \
 && python -m venv --without-pip /opt/openhands-sdk-venv \
 && pip --python /opt/openhands-sdk-venv/bin/python install --no-cache-dir --no-index --find-links /agentdist --require-hashes --no-deps -r /tmp/agent/agent-tools.txt \
 && pip --python /opt/openhands-sdk-venv/bin/python install --no-cache-dir --no-index --find-links /agentdist --require-hashes --no-deps --no-build-isolation -r /tmp/agent/agent-requirements.txt \
 && rm -r /tmp/agent \
 && rm -rf /root/.cache /agentdist
WORKDIR /app/sentry-python
LABEL org.opencontainers.image.source="https://github.com/getsentry/sentry-python" \
      org.opencontainers.image.revision="500f10e79e783754b0dae92119139d2db212602e" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.digest="sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
CMD ["/bin/bash"]
