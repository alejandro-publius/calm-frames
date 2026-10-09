# Evaluation targets: the conformance suite, the baselines, the ablations, and the recipe for
# `reproduce`, which rebuilds every evaluation table and figure offline from what is committed.
#
# Included from the root Makefile, which adds the release lane's half of `reproduce` as a
# prerequisite. It also runs standalone:
#
#   make -f eval/reproduce.mk reproduce
#
# Written for GNU Make 3.81, the version macOS ships.
#
# SAFETY: the conformance targets generate strobes on purpose. Each clip is written to a scratch
# directory outside the repository, analysed and deleted inside the same job, and never opened.
# CALM_CONFORMANCE_SCRATCH says where; the default is under TMPDIR and is never inside media/.
# Do not point it at a directory anything else scans, syncs or backs up.

EVAL_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
EVAL_REPO_DIR := $(patsubst %/,%,$(dir $(EVAL_DIR)))
# The pinned interpreter when there is one, the system one on a clean checkout. The tables need
# nothing but the standard library; the figures need matplotlib, and eval/figures.py says so
# and writes the tables anyway when it is missing.
PY ?= $(shell test -x $(EVAL_REPO_DIR)/.venv/bin/python && echo $(EVAL_REPO_DIR)/.venv/bin/python || echo python3)
RESULTS ?= $(EVAL_REPO_DIR)/results

# Workers for the generate-analyse-delete job. This machine has 8 cores and shares them with a
# Docker VM and a virtual device, so the default is deliberately not 8.
CONFORMANCE_WORKERS ?= 4
# Clips per ablation arm and per cover arm, and these are the numbers the committed
# results/ablations.json was produced with, so `make ablations` reproduces it. Much smaller than
# the suite on purpose: an ablation clip is generated and analysed once for every arm, and the
# few 4K clips in the sample carry about a fifth of the whole cost on their own.
ABLATION_CLIPS ?= 150
COVER_CLIPS ?= 60

.PHONY: reproduce conformance-design conformance conformance-full conformance-report \
        baselines-table ablations realclips-status labeling-pool labeling-plots eval-checks \
        screening-table attribution

reproduce: ## rebuild every evaluation table and figure offline from results/*.json
	$(PY) $(EVAL_DIR)/figures.py

conformance-design: ## write the clip manifest and its ground truth. Fast, no video
	$(PY) $(EVAL_DIR)/conformance/design.py

conformance: $(RESULTS)/conformance_design.json ## generate, analyse and delete clips. Resumable. LIMIT=n for a sample
	$(PY) $(EVAL_DIR)/conformance_resume_guard.py
	$(PY) $(EVAL_DIR)/conformance/generate_analyze.py --workers $(CONFORMANCE_WORKERS) \
		$(if $(LIMIT),--limit $(LIMIT),)

conformance-full: $(RESULTS)/conformance_design.json ## the whole committed design, hours not minutes, then the tables
	$(PY) $(EVAL_DIR)/conformance_resume_guard.py
	$(PY) $(EVAL_DIR)/conformance/generate_analyze.py --workers $(CONFORMANCE_WORKERS)
	$(MAKE) -f $(EVAL_DIR)/reproduce.mk conformance-report baselines-table reproduce

conformance-report: ## score whatever conformance rows exist, offline
	$(PY) $(EVAL_DIR)/conformance/report.py

baselines-table: ## the baseline comparison table, offline: the baselines ran beside each clip
	$(PY) $(EVAL_DIR)/baselines/run_all.py

ablations: ## one detection rule off at a time, the guard band simulation, dim against opaque
	$(PY) $(EVAL_DIR)/ablations/run.py --detection-clips $(ABLATION_CLIPS) \
		--cover-clips $(COVER_CLIPS) --workers $(CONFORMANCE_WORKERS)

labeling-pool: ## the blinded pool and the blank sheets. Nobody labels anything here
	$(PY) $(EVAL_DIR)/labeling/make_pool.py
	$(PY) $(EVAL_DIR)/labeling/make_sheets.py

labeling-plots: ## one plot per pooled segment, with no detector output on any of them
	$(PY) $(EVAL_DIR)/labeling/plots.py

realclips-status: ## what the real clip set is still waiting for
	$(PY) $(EVAL_DIR)/realclips/report.py

screening-table: ## rebuild the per source positives table and the shooting list in screening.json
	$(PY) $(EVAL_DIR)/screening_table.py

attribution: ## rewrite NOTICE and the app's credits screen from media/LICENSES.csv
	$(PY) $(EVAL_DIR)/attribution.py

eval-checks: ## the eval lane's own tests, including the no-flashmap-import guards
	$(PY) -m pytest $(EVAL_DIR)/tests $(EVAL_DIR)/test_plots_standalone.py -q

$(RESULTS)/conformance_design.json:
	$(MAKE) -f $(EVAL_DIR)/reproduce.mk conformance-design
