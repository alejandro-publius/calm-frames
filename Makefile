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

.PHONY: help test test-app test-flashmap test-pipeline test-eval ci \
        reproduce reproduce-release reproduce-all synth cdk-diff deploy destroy \
        release release-notes stick-day stick-day-vvd hooks hooks-selftest \
        scan scan-tree pins clean

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

ci: ## everything CI runs, in CI's order, before you push
	cd $(REPO)/app && $(NODE_ENV) && npm run typecheck
	cd $(REPO)/app && $(NODE_ENV) && npx eslint src test --ext .ts,.tsx
	$(MAKE) test test-eval
	$(MAKE) scan
	$(PY) eval/readme_sync.py --check

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

deploy: ## blocked until HUMAN CHECKPOINT D. Use make synth instead
	@$(REPO)/scripts/aws_guard.sh deploy

destroy: ## blocked by the same rule as deploy
	@$(REPO)/scripts/aws_guard.sh destroy

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

# ----------------------------------------------------------------- house

clean: ## remove build output this Makefile made. Leaves app/build alone
	rm -rf $(REPO)/build/reproduce $(REPO)/build/release
	cd $(REPO)/pipeline/infra && $(MAKE) clean
