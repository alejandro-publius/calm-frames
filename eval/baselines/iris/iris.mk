# IRIS baseline (EA IRIS in Docker). Meant to be included from the root Makefile:
#
#   include eval/baselines/iris/iris.mk
#
#   make iris-build
#   make iris-run VIDEO=path/to/clip.mp4 OUT=path/to/results
#
# iris-run writes OUT/<video file name>/framedata.csv, plus result.json and
# frameData.json when IRIS_ARGS asks for JSON (the default). VIDEO and OUT must
# be paths that Docker can bind-mount (with colima: under your home directory).
# Works with GNU Make 3.81 (the macOS default).

IRIS_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
IRIS_COMMIT := $(shell sed -n 's/^ARG IRIS_COMMIT=//p' $(IRIS_DIR)/Dockerfile)
IRIS_IMAGE ?= calm-frames/iris:$(shell printf '%s' '$(IRIS_COMMIT)' | cut -c1-7)
# Parallel compile jobs inside the build. Changing it rebuilds every layer.
IRIS_BUILD_JOBS ?= 2
# Extra IrisApp flags. "-j 1" writes JSON; add "-p 1" for pattern detection.
IRIS_ARGS ?= -j 1

.PHONY: iris-build iris-run

iris-build:
	docker build --build-arg BUILD_JOBS=$(IRIS_BUILD_JOBS) -t $(IRIS_IMAGE) $(IRIS_DIR)

iris-run:
	@if [ -z "$(VIDEO)" ] || [ -z "$(OUT)" ]; then \
		echo "usage: make iris-run VIDEO=path/to/clip.mp4 OUT=path/to/results" >&2; exit 2; fi
	@case "$(VIDEO)$(OUT)" in *" "*) \
		echo "iris-run: VIDEO and OUT must not contain spaces (make splits on them)" >&2; exit 2;; esac
	@if [ ! -f "$(VIDEO)" ]; then echo "iris-run: no such file: $(VIDEO)" >&2; exit 2; fi
	@mkdir -p "$(OUT)"
	docker run --rm --network none --user "$$(id -u):$$(id -g)" \
		-v "$(abspath $(dir $(VIDEO))):/in:ro" \
		-v "$(abspath $(OUT)):/work/Results" \
		$(IRIS_IMAGE) -v "/in/$(notdir $(VIDEO))" $(IRIS_ARGS)
	@if [ ! -s "$(OUT)/$(notdir $(VIDEO))/framedata.csv" ]; then \
		echo "iris-run: IRIS wrote no results for $(VIDEO)" >&2; exit 1; fi
	@case " $(IRIS_ARGS) " in *" -j 1 "*|*" -j true "*) \
		if [ ! -s "$(OUT)/$(notdir $(VIDEO))/result.json" ]; then \
			echo "iris-run: IRIS wrote no result.json for $(VIDEO)" >&2; exit 1; fi;; esac
	@echo "iris-run: results in $(OUT)/$(notdir $(VIDEO))/"
