# IRIS baseline (EA IRIS). Meant to be included from the root Makefile:
#
#   include eval/baselines/iris/iris.mk
#
#   make iris-native-build                         build IrisApp here, no Docker
#   make iris-pool                                 every clip in media/, through IrisApp
#   make iris-run VIDEO=media/clip.mp4             one clip
#   make iris-selftest                             does the flagging work, both ways
#
# The Docker image is still here and is still the reproducible path on a CI runner:
#
#   make iris-build                                build the pinned image
#   make iris-docker-run VIDEO=... OUT=...         run the image over one clip
#
# It was not used on this Mac. The colima VM is shared with another project and a vcpkg
# source build of the OpenCV tree inside it already pushed it into its memory limit once.
# eval/baselines/iris/build-native.sh builds the same upstream commit against Homebrew
# instead, and says in BUILD_INFO.txt that it did.
#
# iris-docker-run writes OUT/<video file name>/framedata.csv, plus result.json and
# frameData.json when IRIS_ARGS asks for JSON (the default). VIDEO and OUT must be paths
# that Docker can bind-mount (with colima: under your home directory).
# Works with GNU Make 3.81 (the macOS default).

IRIS_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
IRIS_ROOT := $(IRIS_DIR)/../../..
PY ?= $(IRIS_ROOT)/.venv/bin/python
IRIS_COMMIT := $(shell sed -n 's/^ARG IRIS_COMMIT=//p' $(IRIS_DIR)/Dockerfile)
IRIS_IMAGE ?= calm-frames/iris:$(shell printf '%s' '$(IRIS_COMMIT)' | cut -c1-7)
# Parallel compile jobs inside the build. Changing it rebuilds every layer.
IRIS_BUILD_JOBS ?= 2
# Extra IrisApp flags for the Docker path. "-j 1" writes JSON; add "-p 1" for patterns.
IRIS_ARGS ?= -j 1
IRIS_OUT ?= results/baselines/iris
IRIS_RUN_ARGS ?=

.PHONY: iris-build iris-docker-run iris-native-build iris-run iris-pool iris-selftest

iris-native-build:
	sh $(IRIS_DIR)/build-native.sh

iris-run:
	@if [ -z "$(VIDEO)" ]; then \
		echo "usage: make iris-run VIDEO=media/clip.mp4" >&2; exit 2; fi
	@case "$(VIDEO)" in *" "*) echo "VIDEO must not contain spaces" >&2; exit 2;; esac
	$(PY) $(IRIS_DIR)/run.py "$(VIDEO)" -o "$(IRIS_OUT)" $(IRIS_RUN_ARGS)

# Every file in media/, hazard files included. IRIS only decodes and measures them; its one
# imshow call is behind a debug define this build does not set, so nothing is ever shown.
iris-pool:
	@set -e; found=0; \
	for f in media/*.mp4 media/*.mov media/*.webm media/*.ogv media/*.mkv; do \
		[ -e "$$f" ] || continue; found=1; \
		$(PY) $(IRIS_DIR)/run.py "$$f" -o "$(IRIS_OUT)" $(IRIS_RUN_ARGS) || true; \
	done; \
	if [ "$$found" = 0 ]; then echo "no media found; run eval/fetch_media.py first" >&2; exit 2; fi

# Two clips where the right answer is known without any spec:
#   a static mid-gray clip must produce zero segments;
#   a 10 Hz full-field black/white clip must produce at least one.
# The flashing clip is generated, analyzed and deleted inside this target and is never
# opened in a player.
#
# This target deliberately ignores IRIS_RUN_ARGS: it tests the defaults we ship. To confirm
# both directions are live, mutate FLASH_FAIL_FROM in run.py and watch this go red
# (verified Sep 18, 2026: 0 fails on "flagged a clip where nothing happens" because every
# passing frame becomes a flag, 4 fails on "missed a 10 Hz full-field flash" because no
# frame result is ever that high).
iris-selftest:
	@tmp=$$(mktemp -d); \
	ffmpeg -v error -y -f lavfi -i "color=c=0x808080:s=320x240:r=25:d=6" \
		-c:v libx264 -pix_fmt yuv420p "$$tmp/gray_static.mp4"; \
	ffmpeg -v error -y -f lavfi -i "color=c=black:s=320x240:r=50:d=6" \
		-vf "geq=lum='if(gt(mod(floor(T*20),2),0),235,16)':cb=128:cr=128" \
		-c:v libx264 -pix_fmt yuv420p -crf 12 "$$tmp/HAZARD_selftest_flash.mp4"; \
	$(PY) $(IRIS_DIR)/run.py "$$tmp/gray_static.mp4" "$$tmp/HAZARD_selftest_flash.mp4" -o "$$tmp"; \
	calm=$$($(PY) -c "import json,sys;print(json.load(open(sys.argv[1]))['segment_count'])" "$$tmp/gray_static.json"); \
	flash=$$($(PY) -c "import json,sys;print(json.load(open(sys.argv[1]))['segment_count'])" "$$tmp/HAZARD_selftest_flash.json"); \
	rm -rf "$$tmp"; \
	echo "static gray: $$calm segments (want 0).  10 Hz flash: $$flash segments (want >0)."; \
	if [ "$$calm" != "0" ]; then echo "FAIL: flagged a clip where nothing happens" >&2; exit 1; fi; \
	if [ "$$flash" -lt 1 ]; then echo "FAIL: missed a 10 Hz full-field flash" >&2; exit 1; fi; \
	echo "selftest passed"

iris-build:
	docker build --build-arg BUILD_JOBS=$(IRIS_BUILD_JOBS) -t $(IRIS_IMAGE) $(IRIS_DIR)

iris-docker-run:
	@if [ -z "$(VIDEO)" ] || [ -z "$(OUT)" ]; then \
		echo "usage: make iris-docker-run VIDEO=path/to/clip.mp4 OUT=path/to/results" >&2; exit 2; fi
	@case "$(VIDEO)$(OUT)" in *" "*) \
		echo "iris-docker-run: VIDEO and OUT must not contain spaces (make splits on them)" >&2; exit 2;; esac
	@if [ ! -f "$(VIDEO)" ]; then echo "iris-docker-run: no such file: $(VIDEO)" >&2; exit 2; fi
	@mkdir -p "$(OUT)"
	docker run --rm --network none --user "$$(id -u):$$(id -g)" \
		-v "$(abspath $(dir $(VIDEO))):/in:ro" \
		-v "$(abspath $(OUT)):/work/Results" \
		$(IRIS_IMAGE) -v "/in/$(notdir $(VIDEO))" $(IRIS_ARGS)
	@if [ ! -s "$(OUT)/$(notdir $(VIDEO))/framedata.csv" ]; then \
		echo "iris-docker-run: IRIS wrote no results for $(VIDEO)" >&2; exit 1; fi
	@case " $(IRIS_ARGS) " in *" -j 1 "*|*" -j true "*) \
		if [ ! -s "$(OUT)/$(notdir $(VIDEO))/result.json" ]; then \
			echo "iris-docker-run: IRIS wrote no result.json for $(VIDEO)" >&2; exit 1; fi;; esac
	@echo "iris-docker-run: results in $(OUT)/$(notdir $(VIDEO))/"
