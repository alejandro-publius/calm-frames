# Calm Frames infrastructure.
#
# synth and test are safe to run anywhere: they touch no AWS account and need
# no credentials. deploy and destroy are listed so a fresh clone knows the
# commands; the real ones are `make deploy` and `make destroy` at the repository
# root, which wait for HUMAN CHECKPOINT D (the account on the Paid plan and the
# budget alarm in place). The stack was deployed once that way, on Oct 9, 2026.
#
# SIGNING_KEY_PARAMETER names the SSM parameter holding the cloud demo signing
# key. The context below carries it when it is set, the same way
# scripts/aws_guard.sh does, so a diff from here shows the template a deploy
# from the root would send.

PY ?= ../../.venv/bin/python
CDK ?= npx --yes aws-cdk@2.1142.0
STACK ?= CalmFramesStack
BUDGET_EMAIL ?=
GITHUB_REPO ?=
SIGNING_KEY_PARAMETER ?=

CONTEXT = -c calmframes:budgetEmail=$(BUDGET_EMAIL) -c calmframes:githubRepo=$(GITHUB_REPO) \
	$(if $(SIGNING_KEY_PARAMETER),-c calmframes:signingKeyParameter=$(SIGNING_KEY_PARAMETER))

.PHONY: synth test deploy destroy diff clean

synth:
	CDK_DEFAULT_ACCOUNT=$${CDK_DEFAULT_ACCOUNT:-000000000000} \
	CDK_DEFAULT_REGION=$${CDK_DEFAULT_REGION:-us-east-1} \
	$(PY) app.py

test:
	cd ../.. && .venv/bin/python -m pytest pipeline/tests/test_infra.py -q

diff:
	$(CDK) diff $(STACK) $(CONTEXT)

deploy:
	@echo "Deploy is blocked until HUMAN CHECKPOINT D is confirmed."
	@echo "Then: $(CDK) deploy $(STACK) $(CONTEXT)"

destroy:
	@echo "Then: $(CDK) destroy $(STACK)"
	@echo "Every stateful resource is set to Delete, so nothing is left billing."

clean:
	rm -rf cdk.out
