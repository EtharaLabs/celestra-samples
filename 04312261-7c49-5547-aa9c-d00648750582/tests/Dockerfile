# syntax=docker/dockerfile:1.17@sha256:38387523653efa0039f8e1c89bb74a30504e76ee9f565e25c9a09841f9427b05
FROM --platform=$BUILDPLATFORM alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26 AS source
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/pybamm-team/PyBaMM
ARG COMMIT=fe6784fb08d386950d546f75c95849a7edeb5fa8
# The base commit's committer time, so a plain docker build (as Harbor runs it) dates the
# layers it writes the same way a buildx build passing SOURCE_DATE_EPOCH does.
ARG SOURCE_DATE_EPOCH=1792575620
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
COPY binary.txt sdist.txt /req/
RUN case "$TARGETARCH" in amd64) arch=x86_64 ;; arm64) arch=aarch64 ;; *) exit 1 ;; esac \
 && test "$TARGETOS" = linux \
 && pip download --no-cache-dir --require-hashes --only-binary=:all: --no-deps \
      --python-version 3.12 --implementation cp --abi cp312 --abi abi3 --abi none \
      --platform "manylinux_2_28_$arch" --platform "manylinux_2_17_$arch" \
      --platform "manylinux2014_$arch" --platform any \
      -r /req/binary.txt -d /dist \
 && if [ -s /req/sdist.txt ]; then \
      pip install --no-cache-dir --require-hashes --no-deps -r /req/tools.txt \
      && pip download --no-cache-dir --require-hashes --no-binary=:all: --no-deps --no-build-isolation -r /req/sdist.txt -d /dist; \
    fi

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS solvers
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/pybamm-team/PyBaMM
ARG COMMIT=fe6784fb08d386950d546f75c95849a7edeb5fa8
COPY requirements-solvers.txt /req/requirements-solvers.txt
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261022T000000Z bookworm main\ndeb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261022T000000Z bookworm-updates main\ndeb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261022T000000Z bookworm-security main\n' > /etc/apt/sources.list \
 && rm -f /etc/apt/sources.list.d/debian.sources \
 && apt-get -o Acquire::Check-Valid-Until=false update -qq \
 && apt-get install -y -qq --no-install-recommends build-essential=12.9 gfortran=4:12.2.0-3 liblapack-dev=3.11.0-2 libblas-dev=3.11.0-2 git=1:2.39.5-0+deb12u3 ca-certificates=20250419~deb12u2 \
 && rm -rf /var/lib/apt/lists/*
RUN git init -q /src \
 && git -C /src fetch -q --depth 1 "$REPO_URL" "$COMMIT" \
 && git -C /src checkout -q FETCH_HEAD \
 && test "$(git -C /src rev-parse HEAD)" = "$COMMIT" \
 && git -C /src submodule update -q --init --depth 1 packages/pybammsolvers/sundials packages/pybammsolvers/SuiteSparse
RUN pip install --no-cache-dir --require-hashes --no-deps -r /req/requirements-solvers.txt \
 && pip wheel --no-cache-dir --no-deps --no-build-isolation -w /raw /src/packages/pybammsolvers \
 && SOURCE_DATE_EPOCH=1792575620 LD_LIBRARY_PATH=/src/packages/pybammsolvers/.idaklu/lib auditwheel repair --exclude libcasadi.so.3.7 -w /wheels /raw/*.whl

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS runtime
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# In the build environment only: pip then writes hash-checked .pyc files and chage pins the
# account's password-change day, so the layers do not depend on the build date.
ARG SOURCE_DATE_EPOCH=1792575620
# Docker Desktop's Rosetta emulation leaves /root/.cache/rosetta behind every root RUN, so
# each one removes it; a QEMU or native build never writes it.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 SETUPTOOLS_SCM_PRETEND_VERSION=26.10.1.1.dev20
# Without network, litellm (imported by rewardkit) retries its cost-map fetch in a thread whose
# logging races the main import and intermittently crashes rewardkit; use the bundled map.
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
RUN groupadd -g 10001 grader && useradd -u 10001 -g 10001 -m -d /home/grader grader \
 && chage -d "$(date -u -d "@$SOURCE_DATE_EPOCH" +%F)" grader \
 && rm -rf /root/.cache
COPY requirements.txt /tmp/req/
RUN --mount=type=bind,from=wheels,source=/dist,target=/dist \
    pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-build-isolation -r /tmp/req/requirements.txt \
 && rm -r /tmp/req \
 && rm -rf /root/.cache
COPY --from=source /src /grading/repo
RUN pip install --no-cache-dir --no-deps --no-build-isolation --no-index -e /grading/repo/packages/pybamm \
 && rm -rf /root/.cache
RUN --mount=type=bind,from=solvers,source=/wheels,target=/built \
    pip install --no-cache-dir --no-deps --no-index /built/*.whl \
 && rm -rf /root/.cache
COPY graded/ /tests/graded/
# The glob also carries a wrapper's moved original (.trinity-bundle-test.sh), because Harbor
# runs a verifier built from tests/Dockerfile as bundled and never uploads tests/ into it.
COPY judge/ /tests/judge/
COPY *.sh run_graded.py score.py reward.toml test_output.py judge.toml reference.diff combine.py /tests/
RUN chmod 0755 /tests/*.sh \
 && mkdir -p /logs/verifier \
 && chown -R 10001:10001 /grading/repo /logs \
 && rm -rf /root/.cache
WORKDIR /grading/repo
USER 10001:10001
LABEL org.opencontainers.image.source="https://github.com/pybamm-team/PyBaMM" \
      org.opencontainers.image.revision="fe6784fb08d386950d546f75c95849a7edeb5fa8" \
      org.opencontainers.image.licenses="BSD-3-Clause" \
      org.opencontainers.image.base.digest="sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
CMD ["/tests/test.sh"]
