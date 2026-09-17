# ffmpeg photosensitivity baseline. Standalone, or included from a root Makefile:
#
#   make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-run VIDEO=media/clip.mp4
#   make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-pool
#   make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-selftest
#
# Works with GNU Make 3.81 (the macOS default).

FFPS_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
FFPS_ROOT := $(FFPS_DIR)/../../..
PY ?= $(FFPS_ROOT)/.venv/bin/python
FFPS_OUT ?= results/baselines/ffmpeg_photosensitivity
FFPS_ARGS ?=

# Pinned image for the reproducible path. The local ffmpeg is what runs by
# default because the shared colima VM is usually busy with another project.
FFPS_IMAGE ?= jrottenberg/ffmpeg:7.1-ubuntu2404

.PHONY: ffmpeg-ps-run ffmpeg-ps-pool ffmpeg-ps-selftest ffmpeg-ps-version

ffmpeg-ps-run:
	@if [ -z "$(VIDEO)" ]; then \
		echo "usage: make -f $(FFPS_DIR)/ffmpeg_ps.mk ffmpeg-ps-run VIDEO=media/clip.mp4" >&2; exit 2; fi
	@case "$(VIDEO)" in *" "*) echo "VIDEO must not contain spaces" >&2; exit 2;; esac
	$(PY) $(FFPS_DIR)/run.py "$(VIDEO)" -o "$(FFPS_OUT)" $(FFPS_ARGS)

# Every non-hazard and hazard file in media/. Hazard files are only ever read by
# ffmpeg here; nothing is played and nothing is shown.
ffmpeg-ps-pool:
	@set -e; shopt -s nullglob 2>/dev/null || true; \
	found=0; \
	for f in media/*.mp4 media/*.mov media/*.webm media/*.ogv media/*.mkv; do \
		[ -e "$$f" ] || continue; found=1; \
		$(PY) $(FFPS_DIR)/run.py "$$f" -o "$(FFPS_OUT)" $(FFPS_ARGS) || true; \
	done; \
	if [ "$$found" = 0 ]; then echo "no media found; run eval/fetch_media.py first" >&2; exit 2; fi

# Re-measures the claim in run.py's THE FIRST SECOND note: does the filter
# misfire on a clip where nothing happens? Builds a static mid-gray clip, runs
# the detector with the warmup drop turned off, and fails if anything is flagged.
#
# This target deliberately ignores FFPS_ARGS: it tests the defaults we ship, so
# passing FFPS_ARGS on the command line will not change what it checks. To
# confirm the check is live, mutate DEFAULT_DIFF_CODES in run.py and watch this
# go red (verified Sep 17, 2026: -1 gives "150 flagged frames", exit 1).
ffmpeg-ps-selftest:
	@tmp=$$(mktemp -d); \
	ffmpeg -v error -y -f lavfi -i "color=c=0x808080:s=320x240:r=25:d=6" \
		-c:v libx264 -pix_fmt yuv420p "$$tmp/gray_static.mp4"; \
	$(PY) $(FFPS_DIR)/run.py "$$tmp/gray_static.mp4" -o "$$tmp" --warmup 0; \
	n=$$($(PY) -c "import json,sys;print(json.load(open(sys.argv[1]))['flagged_frames'])" "$$tmp/gray_static.json"); \
	echo "static gray clip, warmup drop off: $$n flagged frames"; \
	rm -rf "$$tmp"; \
	if [ "$$n" != "0" ]; then \
		echo "This build DOES misfire on a static clip. Keep the warmup drop and update the note in run.py." >&2; exit 1; \
	else \
		echo "No misfire on this build. run.py's note is still accurate."; \
	fi

ffmpeg-ps-version:
	@ffmpeg -version | head -1
	@ffmpeg -hide_banner -filters | grep photosensitivity || \
		{ echo "this ffmpeg has no photosensitivity filter" >&2; exit 1; }
