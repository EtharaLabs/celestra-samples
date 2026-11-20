# syntax=docker/dockerfile:1.17@sha256:38387523653efa0039f8e1c89bb74a30504e76ee9f565e25c9a09841f9427b05
FROM --platform=$BUILDPLATFORM alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26 AS source
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/fonttools/fonttools
ARG COMMIT=984a5cf614f4b05f0cdd57fc5b5628fd81518805
# The base commit's committer time, so a plain docker build (as Harbor runs it) dates the
# layers it writes the same way a buildx build passing SOURCE_DATE_EPOCH does.
ARG SOURCE_DATE_EPOCH=1787656990
RUN test -n "$SOURCE_DATE_EPOCH" \
 && git init -q /src \
 && git -C /src fetch -q --depth 1 "$REPO_URL" "$COMMIT" \
 && git -C /src checkout -q FETCH_HEAD \
 && test "$(git -C /src rev-parse HEAD)" = "$COMMIT" \
 && rm -rf /src/.git

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

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS runtime
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# In the build environment only: pip then writes hash-checked .pyc files and chage pins the
# account's password-change day, so the layers do not depend on the build date.
ARG SOURCE_DATE_EPOCH=1787656990
# Docker Desktop's Rosetta emulation leaves /root/.cache/rosetta behind every root RUN, so
# each one removes it; a QEMU or native build never writes it.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
# Without network, litellm (imported by rewardkit) retries its cost-map fetch in a thread whose
# logging races the main import and intermittently crashes rewardkit; use the bundled map.
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
RUN groupadd -g 10001 grader && useradd -u 10001 -g 10001 -m -d /home/grader grader \
 && chage -d "$(date -u -d "@$SOURCE_DATE_EPOCH" +%F)" grader \
 && rm -rf /root/.cache
# Kaniko ignores RUN --mount, so these files are copied in and removed by the step that uses them.
COPY --from=wheels /dist /dist
COPY . /ctx
RUN pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-deps -r /ctx/requirements-tools.txt \
 && pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-build-isolation -r /ctx/requirements.txt \
 && rm -rf /root/.cache /dist /ctx
COPY --from=source /src /grading/repo
RUN pip install --no-cache-dir --no-deps --no-build-isolation --no-index --config-settings=editable_mode=compat -e /grading/repo \
 && rm -rf /root/.cache
# The verifier files are copied out of a bind mount and get fixed modes and SOURCE_DATE_EPOCH
# times, so the layer does not depend on the mtimes or modes the build context arrives with.
# The .sh files are matched with find, not a shell glob, which skips dotfiles: that way a
# wrapper's moved original (.trinity-bundle-test.sh) is carried too, because Harbor runs a
# verifier built from tests/Dockerfile as bundled and never uploads tests/ into it.
# Kaniko ignores RUN --mount, so these files are copied in and removed by the step that uses them.
COPY . /ctx
RUN mkdir /tests \
 && cp -R /ctx/graded /ctx/judge /ctx/judge-controls /tests/ \
 && find /ctx -maxdepth 1 -name '*.sh' -exec cp -t /tests/ {} + \
 && cp /ctx/run_graded.py /ctx/score.py /ctx/runner_guard.py /ctx/reward.toml /ctx/test_output.py /ctx/judge.toml /ctx/combine.py /tests/ \
 && find /tests -type d -exec chmod 0755 {} + \
 && find /tests -type f -exec chmod 0644 {} + \
 && find /tests -maxdepth 1 -name '*.sh' -exec chmod 0755 {} + \
 && find /tests -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} + \
 && mkdir -p /logs/verifier \
 && chown -R 10001:10001 /grading/repo /logs \
 && rm -rf /root/.cache /ctx
WORKDIR /grading/repo
# test.sh drops to uid 10001 itself; the image ends as root so Harbor's sandbox can start.
USER root
LABEL org.opencontainers.image.source="https://github.com/fonttools/fonttools" \
      org.opencontainers.image.revision="984a5cf614f4b05f0cdd57fc5b5628fd81518805" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.digest="sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
CMD ["/tests/test.sh"]
