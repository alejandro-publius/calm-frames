# Naive mean-luminance differencing baseline. Standalone, or included from a
# root Makefile:
#
#   make -f eval/baselines/naive_luma_diff/naive_luma.mk naive-luma-run VIDEO=media/clip.mp4
#   make -f eval/baselines/naive_luma_diff/naive_luma.mk naive-luma-pool
#   make -f eval/baselines/naive_luma_diff/naive_luma.mk naive-luma-selftest
#
# Works with GNU Make 3.81 (the macOS default).

NL_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
NL_ROOT := $(NL_DIR)/../../..
PY ?= $(NL_ROOT)/.venv/bin/python
NL_OUT ?= results/baselines/naive_luma_diff
NL_ARGS ?=

.PHONY: naive-luma-run naive-luma-pool naive-luma-selftest

naive-luma-run:
	@if [ -z "$(VIDEO)" ]; then \
		echo "usage: make -f $(NL_DIR)/naive_luma.mk naive-luma-run VIDEO=media/clip.mp4" >&2; exit 2; fi
	@case "$(VIDEO)" in *" "*) echo "VIDEO must not contain spaces" >&2; exit 2;; esac
	$(PY) $(NL_DIR)/run.py "$(VIDEO)" -o "$(NL_OUT)" $(NL_ARGS)

naive-luma-pool:
	@set -e; found=0; \
	for f in media/*.mp4 media/*.mov media/*.webm media/*.ogv media/*.mkv; do \
		[ -e "$$f" ] || continue; found=1; \
		$(PY) $(NL_DIR)/run.py "$$f" -o "$(NL_OUT)" $(NL_ARGS) || true; \
	done; \
	if [ "$$found" = 0 ]; then echo "no media found; run eval/fetch_media.py first" >&2; exit 2; fi

# Two clips where the right answer is known without any spec:
#   a static mid-gray clip must produce zero segments;
#   a 10 Hz full-field black/white clip must produce at least one.
# The flashing clip is generated, analyzed and deleted inside this target and is
# never opened in a player.
#
# This target deliberately ignores NL_ARGS: it tests the defaults we ship, so
# passing NL_ARGS on the command line will not change what it checks. To confirm
# both directions are live, mutate DEFAULT_THRESHOLD in run.py and watch this go
# red (verified Sep 17, 2026: 0.0 fails on "flagged a clip where nothing
# happens", 250.0 fails on "missed a 10 Hz full-field flash").
naive-luma-selftest:
	@tmp=$$(mktemp -d); \
	ffmpeg -v error -y -f lavfi -i "color=c=0x808080:s=320x240:r=25:d=6" \
		-c:v libx264 -pix_fmt yuv420p "$$tmp/gray_static.mp4"; \
	ffmpeg -v error -y -f lavfi -i "color=c=black:s=320x240:r=50:d=6" \
		-vf "geq=lum='if(gt(mod(floor(T*20),2),0),235,16)':cb=128:cr=128" \
		-c:v libx264 -pix_fmt yuv420p -crf 12 "$$tmp/HAZARD_selftest_flash.mp4"; \
	$(PY) $(NL_DIR)/run.py "$$tmp/gray_static.mp4" "$$tmp/HAZARD_selftest_flash.mp4" -o "$$tmp"; \
	calm=$$($(PY) -c "import json,sys;print(json.load(open(sys.argv[1]))['segment_count'])" "$$tmp/gray_static.json"); \
	flash=$$($(PY) -c "import json,sys;print(json.load(open(sys.argv[1]))['segment_count'])" "$$tmp/HAZARD_selftest_flash.json"); \
	rm -rf "$$tmp"; \
	echo "static gray: $$calm segments (want 0).  10 Hz flash: $$flash segments (want >0)."; \
	if [ "$$calm" != "0" ]; then echo "FAIL: flagged a clip where nothing happens" >&2; exit 1; fi; \
	if [ "$$flash" -lt 1 ]; then echo "FAIL: missed a 10 Hz full-field flash" >&2; exit 1; fi; \
	echo "selftest passed"
