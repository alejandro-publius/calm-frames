# Calm Frames: one place to run the whole project.
#
#   make help        every target, with one line each
#   make test        app jest, flashmap pytest, pipeline pytest
#   make reproduce   rebuild every table and figure from committed results
#   make synth       the CDK stack, offline, no AWS account touched
#   make deploy      refuses until HUMAN CHECKPOINT D is confirmed
#   make release     builds the three .vpkg files and stops before publishing
#   make stick-day   unboxing to GATE 1 footage, and the same run on the VVD
#
# Written for GNU Make 3.81, the version macOS ships. No .ONESHELL, no
# .SHELLFLAGS (3.82 and later only), nothing that needs a newer make.

SHELL := /bin/bash

REPO := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
PY ?= $(REPO)/.venv/bin/python
PKG_ID ?= io.github.alejandropublius.calmframes

# The ingest image. DOCKER_BUILD is a variable because a machine that is not
# ARM64 needs buildx to make an ARM64 image:
#   make image DOCKER_BUILD="docker buildx build --platform linux/arm64"
INGEST_IMAGE ?= calm-frames/ingest:local
DOCKER_BUILD ?= docker build

# Node comes from fnm and is pinned by .nvmrc. The Shaka Player build that runs
# during npm install needs a JDK, which is why JAVA_HOME is set for builds and
# left out of test runs that do not need it.
NODE_ENV := source ~/vega/env >/dev/null 2>&1 && eval "$$(fnm env --shell bash)" && fnm use 22 >/dev/null

# Pieces other lanes own, included so `make <their target>` works from the root
# and each file still runs standalone with `make -f <file>`.
#
# eval/reproduce.mk owns the evaluation side of `reproduce` (the conformance
# tables, the baselines, the ablations, the figures) and supplies the recipe for
# the `reproduce` target itself. This file adds the release lane's checks to it
# as a prerequisite further down rather than defining `reproduce` a second time,
# which would override theirs and silently drop their figures.
#
# The leading dash means a missing file is not an error, so a branch without
# theirs still works.
-include eval/reproduce.mk
include eval/baselines/iris/iris.mk
include eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk
include eval/baselines/naive_luma_diff/naive_luma.mk

.DEFAULT_GOAL := help

.PHONY: help test test-app test-flashmap test-pipeline test-eval test-hook-package ci \
        local-library \
        reproduce reproduce-release reproduce-all synth cdk-diff deploy destroy \
        release release-notes stick-day stick-day-vvd hooks hooks-selftest \
        image image-smoke image-context image-push \
        audit audit-check audit-update sbom sbom-check \
        scan scan-tree pins baseline-versions clean

help: ## show this list
	@echo "Calm Frames targets:"
	@# Two comment shapes, because two lanes write these files. This one puts
	@# the description after the target; eval/reproduce.mk puts a ## line above
	@# it. Read both, so one list covers everything.
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'
	@awk '/^## /{line = substr($$0, 4); next} \
	     /^[a-zA-Z0-9_-]+:/{if (line != "") {split($$0, name, ":"); \
	       printf "  %-18s %s\n", name[1], line}; line = ""} \
	     !/^##/{line = ""}' $(MAKEFILE_LIST) | sort
	@echo
	@echo "Useful variables:"
	@echo "  PY=$(PY)"
	@echo "  STICK_DAY_ARGS   passed to scripts/stick_day.py (try --help)"
	@echo "  RELEASE_ARGS     passed to scripts/release.sh (try --help)"

# ---------------------------------------------------------------- tests

test: test-app test-flashmap test-pipeline ## app jest, flashmap pytest, pipeline pytest

test-app: ## the Vega app's jest suite, the same command CI runs
	cd $(REPO)/app && $(NODE_ENV) && npx jest --colors=false --ci

test-flashmap: ## flashmap pytest, skipping the slow conformance suite
	cd $(REPO) && $(PY) -m pytest flashmap -q -m "not slow"

test-pipeline: ## pipeline pytest, including the CDK unit tests
	cd $(REPO) && $(PY) -m pytest pipeline -q -m "not slow"

test-eval: ## the standalone eval tests, which CI also runs
	cd $(REPO) && $(PY) -m pytest eval -q -m "not slow"

test-hook-package: ## pack and check a clean offline hook consumer with current Vega peers
	cd $(REPO) && $(NODE_ENV) && npm --prefix hook run test:package
	cd $(REPO) && $(NODE_ENV) && npm --prefix hook run check:package

local-library: ## prepare a verified local title, using LOCAL_LIBRARY_ARGS (no AWS)
	cd $(REPO) && $(PY) -m pipeline.local_library $(LOCAL_LIBRARY_ARGS)

ci: ## everything CI runs, in CI's order, before you push
	cd $(REPO)/app && $(NODE_ENV) && npm run typecheck
	cd $(REPO)/app && $(NODE_ENV) && npx eslint src test --ext .ts,.tsx
	$(MAKE) test test-eval test-hook-package
	$(MAKE) scan
	$(PY) eval/readme_sync.py --check
	# The audit workflow's jobs, in its order. These reach the public advisory
	# databases and the npm registry, so they are the slow part of this target,
	# and leaving them out would make the name of this target a lie.
	$(MAKE) audit-check sbom-check
	$(PY) -m pytest pipeline/tests/test_infra.py pipeline/tests/test_infra_ingest.py \
		pipeline/tests/test_aws_guard.py -q

# ------------------------------------------------------------ reproduce

# `reproduce` has its recipe in eval/reproduce.mk: the eval lane's tables and
# figures. A target can carry prerequisites in one file and its recipe in
# another, so this adds the release lane's half in front of theirs without
# overriding anything. Both halves run, in this order, from one command.
reproduce: reproduce-release $(REPRODUCE_EXTRA)

reproduce-release: ## the release lane's half of reproduce, on its own
	$(PY) $(REPO)/scripts/reproduce.py $(REPRODUCE_ARGS)

reproduce-all: ## reproduce, plus the pieces that need the media pool
	$(MAKE) reproduce REPRODUCE_ARGS="--with-baselines --with-screening"

# ------------------------------------------------------------------ AWS
#
# Nothing here calls AWS. synth writes a template from the code and never needs
# credentials. deploy and destroy go through scripts/aws_guard.sh, which
# refuses until docs/STATUS.md records the Paid plan and the operator sets
# CHECKPOINT_D=confirmed on the command line.

synth: ## synthesize the CDK stack offline, no credentials, no account
	# Two things this adds to pipeline/infra's own synth target:
	#   Node 22 from fnm, not the system Node. The CDK runs its Python code
	#   through jsii, which shells out to node, and the system node here is 26,
	#   which jsii warns it has never been tested with.
	#   CDK_OUTDIR, because an App with no outdir synthesizes into a temporary
	#   directory that is gone before anyone can read the template.
	cd $(REPO)/pipeline/infra && $(NODE_ENV) && CDK_OUTDIR=cdk.out $(MAKE) synth
	@echo
	@echo "Template written to pipeline/infra/cdk.out:"
	@ls -1 $(REPO)/pipeline/infra/cdk.out | sed 's/^/  /'
	@echo
	@echo "Nothing called AWS. No credentials were read."
	@grep -c '"AWS::EC2::NatGateway"' $(REPO)/pipeline/infra/cdk.out/CalmFramesStack.template.json \
		| sed 's/^/  NAT gateways in the template: /' || true

cdk-diff: ## cdk diff, which does reach AWS, so it is behind the same guard
	@$(REPO)/scripts/aws_guard.sh diff

# One command, two steps: the stack, then the image the task runs. The stack
# comes first because the image is pushed to the ECR repository the stack makes.
# If the first step refuses, make stops and the second never runs.
deploy: ## blocked until HUMAN CHECKPOINT D. Use make synth instead
	@$(REPO)/scripts/aws_guard.sh deploy
	@$(REPO)/scripts/aws_guard.sh image

destroy: ## blocked by the same rule as deploy
	@$(REPO)/scripts/aws_guard.sh destroy

# ------------------------------------------------------- the ingest image
#
# Building bills nobody, so `image` runs today. Only `image-push` reaches an
# account, and it waits behind the same two locks as deploy.

image: ## build the ingest container for ARM64. No AWS, no account
	cd $(REPO) && DOCKER_BUILDKIT=0 $(DOCKER_BUILD) \
		-f pipeline/infra/ingest/Dockerfile -t $(INGEST_IMAGE) .
	@echo
	@docker image inspect $(INGEST_IMAGE) \
		--format 'built {{.Architecture}}/{{.Os}}, {{len .RootFS.Layers}} layers, {{.Size}} bytes'

image-smoke: ## run the image with no credentials and read what it refuses
	docker run --rm $(INGEST_IMAGE) ; \
	  echo "exit $$? (2 is right: nothing is configured, so it refuses to start)"

image-context: ## every file the build would send to the daemon
	@$(PY) $(REPO)/scripts/build_context.py

image-push: ## build and push to ECR. Blocked until HUMAN CHECKPOINT D
	@$(REPO)/scripts/aws_guard.sh image

# --------------------------------------------------------------- audits
#
# Both of these reach the public advisory databases and the npm registry. They
# reach nothing private, and no AWS account.

audit: ## pip-audit and npm audit, with every exception written down
	@$(NODE_ENV) && $(PY) $(REPO)/scripts/dep_audit.py $(AUDIT_ARGS)

audit-check: ## the same, and fail if a finding has no exception
	@$(NODE_ENV) && $(PY) $(REPO)/scripts/dep_audit.py --check $(AUDIT_ARGS)

audit-update: ## refresh the advisory ids in scripts/audit_exceptions.toml
	@$(NODE_ENV) && $(PY) $(REPO)/scripts/dep_audit.py --update-ids $(AUDIT_ARGS)

sbom: ## write the CycloneDX bills of materials into docs/
	@$(NODE_ENV) && $(PY) $(REPO)/scripts/sbom.py

sbom-check: ## fail if a committed bill no longer matches what is installed
	@$(NODE_ENV) && $(PY) $(REPO)/scripts/sbom.py --check

# -------------------------------------------------------------- release

release: ## build armv7, aarch64 and x86_64 .vpkg files and stop before publishing
	@$(REPO)/scripts/release.sh $(RELEASE_ARGS)

release-notes: ## the release notes and attachment list, without rebuilding
	@$(REPO)/scripts/release.sh --skip-build $(RELEASE_ARGS)

# ------------------------------------------------------------ stick day

stick-day: ## unboxing to GATE 1 footage: dev mode, OS check, install, layering, markers
	$(PY) $(REPO)/scripts/stick_day.py $(STICK_DAY_ARGS)

stick-day-vvd: ## the same run against the Vega Virtual Device, to prove it
	$(PY) $(REPO)/scripts/stick_day.py --target vvd $(STICK_DAY_ARGS)

# --------------------------------------------------------------- secrets

hooks: ## install the gitleaks pre-commit hook into this checkout
	@$(REPO)/scripts/install_hooks.sh

hooks-selftest: ## watch the pre-commit hook block a planted key, in a throwaway repo
	@$(REPO)/scripts/hook_selftest.sh

scan: ## gitleaks over the committed tree, the same scan CI runs
	@$(REPO)/scripts/gitleaks_scan.sh committed

scan-tree: ## gitleaks over the whole working directory, including ignored files
	@$(REPO)/scripts/gitleaks_scan.sh tree

pins: ## report any dependency version that is not pinned
	@$(PY) $(REPO)/scripts/check_pins.py

baseline-versions: ## fail if a baseline results directory holds two tool versions
	@$(PY) $(REPO)/eval/baseline_versions.py --list

# ------------------------------------------------------- the camera meter
#
# eval/meter.py reads a filmed TV screen and counts WCAG flashes inside it.
# Two targets drive it: one turns a session's recordings into numbers, the
# other re-runs the meter's own validation against simulated footage.
#
# SAFETY: meter-validate renders strobes on purpose. Every clip is written to a
# scratch directory outside the repository, measured and deleted inside the
# same job, and never opened. CALM_METER_SCRATCH says where; the default is
# under TMPDIR and is never inside media/.

.PHONY: ingest-recordings meter-validate

ingest-recordings: ## screen-level recordings -> results/screen_level.json. Refuses when there are none
	$(PY) $(REPO)/eval/meter_ingest.py $(INGEST_ARGS)

meter-validate: ## re-measure the meter on simulated footage. Half an hour, writes results/meter_validation.json
	$(PY) $(REPO)/eval/meter_validate.py $(METER_VALIDATE_ARGS)

# ------------------------------------------------------------- hardening
#
# The mutation gate, the property tests and the map fuzz corpus. These are what
# stop a green suite from meaning nothing: every safety guard is broken on
# purpose and its test has to go red, and every property is stated over random
# input rather than one fixture.
#
# Python comes from the checkout's virtual environment on this machine and from
# python3 in CI, where there is none. Node comes from fnm here and from the
# runner's PATH in CI, and neither target fails just because fnm is absent.

HARDEN_PY := $(shell [ -x "$(REPO)/.venv/bin/python" ] && echo "$(REPO)/.venv/bin/python" || command -v python3)
NODE_ANY := if command -v fnm >/dev/null 2>&1; then eval "$$(fnm env --shell bash)" >/dev/null 2>&1 && fnm use 22 >/dev/null 2>&1 || true; fi

PROPERTY_TESTS := eval/property_scheduler_test.py eval/property_drift_test.py \
                  eval/fuzz_maps_test.py

.PHONY: mutate properties fuzz drift harden

mutate: ## break every safety guard on purpose, watch its test go red, write results/mutation.json
	cd $(REPO) && $(NODE_ANY); $(HARDEN_PY) eval/mutate_gate.py $(MUTATE_ARGS)

properties: ## hypothesis property tests for the scheduler, the windows and the map readers
	cd $(REPO) && $(NODE_ANY); $(HARDEN_PY) eval/property_runner.py
	cd $(REPO) && $(NODE_ANY); CALM_FRAMES_REQUIRE_NODE=1 \
		$(HARDEN_PY) -m pytest $(PROPERTY_TESTS) eval/property_windows_test.py -q

fuzz: ## replay eval/fuzz_corpus through all three map readers, write results/fuzz.json
	cd $(REPO) && $(NODE_ANY); $(HARDEN_PY) eval/fuzz_maps_test.py

drift: ## the two hour clock drift run against the real scheduler, write results/drift.json
	cd $(REPO) && $(NODE_ANY); $(HARDEN_PY) eval/property_drift_test.py

harden: properties fuzz drift mutate ## everything in this section, in the order that fails fastest

# ----------------------------------------------------------------- house

clean: ## remove build output this Makefile made. Leaves app/build alone
	rm -rf $(REPO)/build/reproduce $(REPO)/build/release
	cd $(REPO)/pipeline/infra && $(MAKE) clean
