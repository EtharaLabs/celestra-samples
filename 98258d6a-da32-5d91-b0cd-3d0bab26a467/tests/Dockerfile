# syntax=docker/dockerfile:1.17@sha256:38387523653efa0039f8e1c89bb74a30504e76ee9f565e25c9a09841f9427b05
FROM --platform=$BUILDPLATFORM alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26 AS source
SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ARG REPO_URL=https://github.com/PyPSA/PyPSA
ARG COMMIT=6d1da8049b3346969bc8f2b97f7835dc0b7c6fbe
# The base commit's committer time, so a plain docker build (as Harbor runs it) dates the
# layers it writes the same way a buildx build passing SOURCE_DATE_EPOCH does.
ARG SOURCE_DATE_EPOCH=1787045920
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
ARG SOURCE_DATE_EPOCH=1787045920
# Docker Desktop's Rosetta emulation leaves /root/.cache/rosetta behind every root RUN, so
# each one removes it; a QEMU or native build never writes it.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYPSA=1.2.5.dev66 LINOPY_SEMANTICS=v1 XDG_CACHE_HOME=/opt/cache
ADD --chown=10001:10001 --checksum=sha256:cb544411ca5900f9398ac75794065e0c6d58e91f44ab65b9d2be981beedf37e7 https://data.pypsa.org/networks/examples/v1.2.4/ac_dc_meshed.nc /opt/cache/pypsa/examples/v1.2.5/ac_dc_meshed.nc
ADD --chown=10001:10001 --checksum=sha256:6b4ffd111b9dfed0fe14ce725e5e06cc69c29e4221c4f60bd265f760a9622ad2 https://data.pypsa.org/networks/examples/v1.2.4/model_energy.nc /opt/cache/pypsa/examples/v1.2.5/model_energy.nc
ADD --chown=10001:10001 --checksum=sha256:37e654247b62019bd8939e1633c7a25cbe447975181b375a7f29aedc44105bdc https://data.pypsa.org/networks/examples/v1.2.4/scigrid_de.nc /opt/cache/pypsa/examples/v1.2.5/scigrid_de.nc
ADD --chown=10001:10001 --checksum=sha256:af6c30e744b2823c9782ddae12127618934969c721b6a70c7f7676b7d1bb8cf1 https://data.pypsa.org/networks/examples/v1.2.4/stochastic_network.nc /opt/cache/pypsa/examples/v1.2.5/stochastic_network.nc
ADD --chown=10001:10001 --checksum=sha256:9bfbeb3637d85a64aa2fe0e1820bdffd401ec7f939438c4c833ec745f2f6dfd7 https://data.pypsa.org/networks/examples/v1.2.4/storage_hvdc.nc /opt/cache/pypsa/examples/v1.2.5/storage_hvdc.nc
# Without network, litellm (imported by rewardkit) retries its cost-map fetch in a thread whose
# logging races the main import and intermittently crashes rewardkit; use the bundled map.
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
RUN groupadd -g 10001 grader && useradd -u 10001 -g 10001 -m -d /home/grader grader \
 && chage -d "$(date -u -d "@$SOURCE_DATE_EPOCH" +%F)" grader \
 && rm -rf /root/.cache
COPY requirements-tools.txt requirements.txt /tmp/req/
# Kaniko ignores RUN --mount, so these files are copied in and removed by the step that uses them.
COPY --from=wheels /dist /dist
RUN pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-deps -r /tmp/req/requirements-tools.txt \
 && pip install --no-cache-dir --no-index --find-links /dist --require-hashes --no-build-isolation -r /tmp/req/requirements.txt \
 && rm -r /tmp/req \
 && rm -rf /root/.cache /dist
COPY --from=source /src /grading/repo
RUN pip install --no-cache-dir --no-deps --no-build-isolation --no-index -e /grading/repo \
 && rm -rf /root/.cache
COPY graded/ /tests/graded/
COPY judge/ /tests/judge/
COPY judge-controls/ /tests/judge-controls/
# The glob also carries a wrapper's moved original (.trinity-bundle-test.sh), because Harbor
# runs a verifier built from tests/Dockerfile as bundled and never uploads tests/ into it.
COPY *.sh run_graded.py score.py option_guard.py reward.toml test_output.py judge.toml combine.py /tests/
# combine.py ships as 0644 (delivery allows 0755 only on *.sh); restore its exec bit in the image.
RUN chmod 0755 /tests/*.sh /tests/combine.py \
 && mkdir -p /logs/verifier \
 && chown -R 10001:10001 /grading/repo /logs \
 && rm -rf /root/.cache
WORKDIR /grading/repo
# test.sh drops to uid 10001 itself; the image ends as root so Harbor's sandbox can start.
USER root
LABEL org.opencontainers.image.source="https://github.com/PyPSA/PyPSA" \
      org.opencontainers.image.revision="6d1da8049b3346969bc8f2b97f7835dc0b7c6fbe" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.digest="sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
CMD ["/tests/test.sh"]
