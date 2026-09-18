"""Property tests for the cover scheduler, against the app's own TypeScript.

The scheduler is the piece GATE 1 measures, so these tests drive the real modules in
app/src/calmframes rather than a Python copy of them. A copy would only ever test itself.
eval/property_runner.py compiles them with the app's tsc and keeps one node process alive,
so hypothesis can ask a few hundred questions a second.

What is stated here, and why each one is a safety property rather than a preference:

* every flagged millisecond is hidden, at any guard band, any minimum cover and any
  rendition offset;
* the cover is on a full guard band before the flashing starts;
* intervals come out sorted and never touch, so the cover cannot blink off between two
  segments that nearly meet;
* red survives merging, because a dim cover does not satisfy WCAG's red rule;
* a wider guard band hides everything a narrower one hid, so no setting can subtract cover;
* a seek that lands in a flagged span, or decodes from one, covers before it moves;
* the seek engine never uncovers at a position that is inside an interval;
* over a whole timeline, with rate changes, stalls, pauses and seeks, a real playhead inside
  a flagged span is hidden whenever the estimate is out by no more than the guard band. That
  last one is the theorem the wall-clock design rests on, and its converse is the reason the
  guard band exists at all.

Run them with `make properties`, which compiles the scheduler first and turns a missing node
into a failure rather than a skip.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from property_runner import scheduler  # noqa: F401  (the session fixture)

SETTINGS = settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

# Segments start at least three seconds in, so that the schedule's clamp at zero is never what
# decides the answer. The clamp has its own test in app/test/calmframes/coverSchedule.test.ts.
segment_rows = st.lists(
    st.tuples(
        st.integers(min_value=3_000, max_value=600_000),
        st.integers(min_value=1, max_value=20_000),
        st.sampled_from(["general", "red"]),
    ),
    min_size=1,
    max_size=8,
)

guard_bands = st.integers(min_value=0, max_value=2_000)
min_covers = st.integers(min_value=0, max_value=2_000)
# The app refuses anything past MAX_RENDITION_START_OFFSET_MS, so the range stops where
# pipeline/verify.py's START_OFFSET_LIMIT_MS does.
offsets = st.integers(min_value=-150, max_value=150)


def as_segments(rows) -> list[dict]:
    return [
        {"startMs": start, "endMs": start + length, "reason": reason}
        for start, length, reason in rows
    ]


def ask(scheduler, job: dict) -> dict:
    answer = scheduler.call(job)
    assert answer["ok"], answer.get("error")
    return answer


@given(rows=segment_rows, guard=guard_bands, min_cover=min_covers, offset=offsets)
@SETTINGS
def test_every_flagged_millisecond_is_hidden(scheduler, rows, guard, min_cover, offset):
    segments = as_segments(rows)
    options = {"guardBandMs": guard, "minCoverMs": min_cover, "renditionStartOffsetMs": offset}
    times = []
    for segment in segments:
        start = segment["startMs"] - offset
        end = segment["endMs"] - offset
        times.extend([start, (start + end) // 2, end - 1])
    answer = ask(scheduler, {"job": "covered", "segments": segments, "options": options, "times": times})
    missed = [time for time, hidden in zip(times, answer["covered"]) if not hidden]
    assert not missed, f"these flagged moments were not hidden: {missed}"


@given(rows=segment_rows, guard=guard_bands, min_cover=min_covers, offset=offsets)
@SETTINGS
def test_the_cover_is_on_a_whole_guard_band_early(scheduler, rows, guard, min_cover, offset):
    segments = as_segments(rows)
    options = {"guardBandMs": guard, "minCoverMs": min_cover, "renditionStartOffsetMs": offset}
    times = [segment["startMs"] - offset - guard for segment in segments]
    answer = ask(scheduler, {"job": "covered", "segments": segments, "options": options, "times": times})
    late = [time for time, hidden in zip(times, answer["covered"]) if not hidden]
    assert not late, f"the cover was not yet on a guard band before: {late}"


@given(rows=segment_rows, guard=guard_bands, min_cover=min_covers)
@SETTINGS
def test_intervals_come_out_sorted_and_never_touch(scheduler, rows, guard, min_cover):
    segments = as_segments(rows)
    answer = ask(
        scheduler,
        {
            "job": "schedule",
            "segments": segments,
            "options": {"guardBandMs": guard, "minCoverMs": min_cover},
        },
    )
    intervals = answer["intervals"]
    for earlier, later in zip(intervals, intervals[1:]):
        assert earlier["endMs"] < later["startMs"], (
            "two intervals touch or overlap, so the cover would blink off between them: "
            f"{earlier} then {later}"
        )
    for interval in intervals:
        assert interval["endMs"] > interval["startMs"]


def test_two_intervals_that_meet_at_a_point_are_merged(scheduler):
    """The exact touch, pinned rather than left to chance.

    The merge above is written `interval.startMs <= previous.endMs`. Written `<`
    instead, two intervals that meet at exactly one point stop merging, and the
    cover blinks off for a frame between two flagged spans.

    test_intervals_come_out_sorted_and_never_touch would catch that, but only if
    hypothesis happens to draw a pair that lands on the same millisecond after
    widening, at whichever guard band it drew. Over thirty examples it does not,
    and the mutation gate found that out: `property-intervals-never-touch`
    survived with every one of those tests passing. So the case is written down.

    With a 500 ms band, a segment ending at 2000 widens to 2500 and one starting
    at 3000 widens to 2500 as well. They meet, and the answer has to be one
    interval covering both.
    """
    answer = ask(
        scheduler,
        {
            "job": "schedule",
            "segments": as_segments([(1_000, 1_000, "general"), (3_000, 1_000, "general")]),
            "options": {"guardBandMs": 500, "minCoverMs": 0},
        },
    )
    intervals = answer["intervals"]
    assert len(intervals) == 1, (
        "two spans that meet at exactly one millisecond came back as separate "
        f"intervals, so the cover blinks off between them: {intervals}"
    )
    assert intervals[0]["startMs"] == 500
    assert intervals[0]["endMs"] == 4_500


@given(rows=segment_rows, guard=guard_bands, min_cover=min_covers)
@SETTINGS
def test_any_red_source_makes_the_whole_interval_red(scheduler, rows, guard, min_cover):
    segments = as_segments(rows)
    answer = ask(
        scheduler,
        {
            "job": "schedule",
            "segments": segments,
            "options": {"guardBandMs": guard, "minCoverMs": min_cover},
        },
    )
    for interval in answer["intervals"]:
        if any(source.get("reason") == "red" for source in interval["sources"]):
            assert interval["reason"] == "red", (
                "an interval with a red segment in it came out general, and a dim cover does "
                f"not satisfy the red rule: {interval}"
            )


@given(
    rows=segment_rows,
    narrow=guard_bands,
    extra=st.integers(min_value=0, max_value=2_000),
    min_cover=min_covers,
)
@SETTINGS
def test_a_wider_guard_band_hides_everything_the_narrower_one_did(
    scheduler, rows, narrow, extra, min_cover
):
    """No household setting may subtract cover.

    Stated over the span the narrow band itself promises, which is the segment plus that band.
    The minimum cover length is deliberately left out of the claim: it pads a very short
    interval to stop the cover flickering, and a wider band can reach that minimum without the
    padding, so the padded tail of the narrow schedule can end later than the wide one's. The
    flagged span and its band are covered either way, which is the part that is about safety.
    test_the_minimum_cover_tail_is_not_monotone records the other half on purpose.
    """
    segments = as_segments(rows)
    wide = narrow + extra
    times = []
    for segment in segments:
        times.extend(
            [
                max(0, segment["startMs"] - narrow),
                segment["startMs"],
                segment["endMs"] - 1,
                segment["endMs"] + narrow - 1,
            ]
        )
    narrow_answer = ask(
        scheduler,
        {
            "job": "covered",
            "segments": segments,
            "options": {"guardBandMs": narrow, "minCoverMs": min_cover},
            "times": times,
        },
    )
    wide_answer = ask(
        scheduler,
        {
            "job": "covered",
            "segments": segments,
            "options": {"guardBandMs": wide, "minCoverMs": min_cover},
            "times": times,
        },
    )
    lost = [
        time
        for time, was, now in zip(times, narrow_answer["covered"], wide_answer["covered"])
        if was and not now
    ]
    assert not lost, f"a wider guard band stopped hiding: {lost}"


def test_the_minimum_cover_tail_is_not_monotone(scheduler):
    """A found quirk, written down rather than left to be rediscovered.

    Widening the guard band can make the cover END EARLIER for a very short segment, because
    the minimum cover length is reached by growing the end from the start: a narrow band needs
    more padding to reach it than a wide one does. Nothing flagged is left showing, so this is
    about flicker and not about safety, but a reader who assumes "wider is always longer"
    would be wrong and should find out here.
    """
    segments = [{"startMs": 10_000, "endMs": 10_100, "reason": "general"}]
    narrow = ask(
        scheduler,
        {"job": "schedule", "segments": segments, "options": {"guardBandMs": 0, "minCoverMs": 2_000}},
    )["intervals"]
    wide = ask(
        scheduler,
        {"job": "schedule", "segments": segments, "options": {"guardBandMs": 500, "minCoverMs": 2_000}},
    )["intervals"]
    assert narrow[0]["endMs"] == 12_000
    assert wide[0]["endMs"] == 11_500
    assert wide[0]["startMs"] < narrow[0]["startMs"]
    # The flagged span itself is inside both, which is the part that matters.
    for intervals in (narrow, wide):
        assert intervals[0]["startMs"] <= 10_000 and intervals[0]["endMs"] >= 10_100


@given(
    rows=segment_rows,
    guard=guard_bands,
    offsets_into=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=6),
    source=st.sampled_from(
        ["seek-bar", "dpad-fast-forward", "dpad-rewind", "trickplay", "media-control"]
    ),
)
@SETTINGS
def test_a_seek_into_a_hidden_span_covers_before_it_moves(
    scheduler, rows, guard, offsets_into, source
):
    segments = as_segments(rows)
    built = ask(
        scheduler,
        {"job": "schedule", "segments": segments, "options": {"guardBandMs": guard}},
    )["intervals"]
    assume(built)
    targets = []
    for fraction in offsets_into:
        interval = built[int(fraction * (len(built) - 1))]
        span = interval["endMs"] - interval["startMs"]
        targets.append(int(interval["startMs"] + fraction * (span - 1)))
    answer = ask(
        scheduler,
        {
            "job": "plans",
            "segments": segments,
            "options": {"guardBandMs": guard},
            "targets": targets,
            "source": source,
        },
    )
    for target, plan in zip(targets, answer["plans"]):
        assert plan["coverFirst"], f"a seek to {target} did not cover first: {plan['reason']}"


@given(rows=segment_rows, guard=guard_bands, gap=st.integers(min_value=1, max_value=1_999))
@SETTINGS
def test_a_seek_just_past_a_hidden_span_still_covers_first(scheduler, rows, guard, gap):
    """A seek decodes from the keyframe at or before the target, so a target a moment after an
    interval can still put a frame from inside it on screen."""
    segments = as_segments(rows)
    built = ask(
        scheduler,
        {"job": "schedule", "segments": segments, "options": {"guardBandMs": guard}},
    )["intervals"]
    assume(built)
    targets = [int(interval["endMs"] + gap) for interval in built]
    answer = ask(
        scheduler,
        {
            "job": "plans",
            "segments": segments,
            "options": {"guardBandMs": guard},
            "targets": targets,
        },
    )
    for target, plan in zip(targets, answer["plans"]):
        assert plan["coverFirst"], (
            f"a seek to {target}, {gap} ms after an interval ended, did not cover first, so "
            "the decoder could show a frame from inside it"
        )


@given(
    rows=segment_rows,
    guard=guard_bands,
    script=st.lists(
        st.one_of(
            st.tuples(st.just("seek"), st.integers(min_value=0, max_value=650_000)),
            st.tuples(st.just("report"), st.integers(min_value=0, max_value=650_000)),
        ),
        min_size=1,
        max_size=20,
    ),
)
@SETTINGS
def test_the_seek_engine_never_uncovers_inside_an_interval(scheduler, rows, guard, script):
    segments = as_segments(rows)
    steps = [
        {"kind": kind, "targetMs": value} if kind == "seek" else {"kind": kind, "mediaTimeMs": value}
        for kind, value in script
    ]
    answer = ask(
        scheduler,
        {
            "job": "seekRun",
            "segments": segments,
            "options": {"guardBandMs": guard},
            "script": steps,
        },
    )
    intervals = answer["intervals"]

    def inside(time: float) -> bool:
        return any(i["startMs"] <= time < i["endMs"] for i in intervals)

    for call in answer["calls"]:
        if not call["on"]:
            assert not inside(call["at"]), (
                f"the cover came off at {call['at']}, which is inside an interval: {call['reason']}"
            )


@given(
    rows=segment_rows,
    guard=st.integers(min_value=250, max_value=2_000),
    rate=st.sampled_from([0.5, 1.0, 1.25, 2.0]),
    report_every=st.integers(min_value=100, max_value=6_000),
    drift=st.floats(min_value=0.98, max_value=1.02),
    stall_at=st.integers(min_value=5_000, max_value=90_000),
    stall_for=st.integers(min_value=0, max_value=8_000),
    seek_to=st.integers(min_value=0, max_value=200_000),
)
@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_a_real_playhead_in_a_flagged_span_is_hidden_while_the_estimate_is_within_the_band(
    scheduler, rows, guard, rate, report_every, drift, stall_at, stall_for, seek_to
):
    """The theorem the wall-clock design rests on.

    The scheduler runs ahead of the player on a wall clock, so its idea of the playhead is
    always a little wrong. The claim is not that it is never wrong: it is that being wrong by
    no more than the guard band cannot leave a flagged frame showing. Every tick where the
    real playhead is inside a flagged span and the picture was NOT hidden has to be a tick
    where the estimate was out by more than the band.
    """
    segments = as_segments(rows)
    end = 120_000
    phases = [
        {"untilWallMs": stall_at, "kind": "play", "rate": rate},
        {"untilWallMs": stall_at + stall_for, "kind": "stall"},
        {"untilWallMs": end, "kind": "play", "rate": rate},
    ]
    answer = ask(
        scheduler,
        {
            "job": "scheduleRun",
            "segments": segments,
            "options": {"guardBandMs": guard, "minCoverMs": 400},
            "phases": phases,
            "seeks": [{"atWallMs": end // 2, "toMediaMs": seek_to}],
            "endWallMs": end,
            "reportEveryMs": report_every,
            "driftFactor": drift,
        },
    )
    for moment in answer["uncoveredAt"]:
        assert abs(moment["errorMs"]) > guard, (
            "a flagged frame was showing while the estimate was inside the guard band, "
            f"which the design says cannot happen: {moment}, guard band {guard} ms"
        )


@given(
    rows=segment_rows,
    guard=st.integers(min_value=250, max_value=2_000),
    rate=st.sampled_from([0.5, 1.0, 2.0]),
)
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_a_stall_hides_the_picture_and_keeps_it_hidden(scheduler, rows, guard, rate):
    """A stall makes the playhead uncertain, and uncertain means hidden, whatever the
    schedule says. Nothing in the stall window may be showing."""
    segments = as_segments(rows)
    answer = ask(
        scheduler,
        {
            "job": "scheduleRun",
            "segments": segments,
            "options": {"guardBandMs": guard},
            "phases": [
                {"untilWallMs": 10_000, "kind": "play", "rate": rate},
                {"untilWallMs": 40_000, "kind": "stall"},
            ],
            "endWallMs": 40_000,
            "reportEveryMs": 400,
        },
    )
    stalled = [
        moment for moment in answer["uncoveredAt"] if 10_000 <= moment["wallMs"] <= 40_000
    ]
    assert not stalled, f"the picture was showing during a stall: {stalled[:3]}"


@given(
    rows=segment_rows,
    rate=st.sampled_from([0.5, 1.0, 1.25, 2.0]),
    report_every=st.integers(min_value=100, max_value=6_000),
    stall_at=st.integers(min_value=5_000, max_value=90_000),
    stall_for=st.integers(min_value=0, max_value=8_000),
    seek_to=st.integers(min_value=0, max_value=200_000),
)
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_the_estimate_matches_the_player_when_nothing_drifts(
    scheduler, rows, rate, report_every, stall_at, stall_for, seek_to
):
    """A player whose clock runs at exactly the rate it reports leaves the estimate nowhere
    to go wrong.

    Rate changes, a stall and a seek all go past, and the estimate still tracks the playhead,
    because every one of them re-anchors the clock rather than carrying on from where it was.
    Whatever error the scheduler has is drift, not arithmetic, and this is the test that says
    so.

    The bound is one tick of media time rather than zero, and that is the simulator's fault
    rather than the scheduler's: a phase only starts or ends on a tick, so a stall asked for
    at 5,000 ms begins at 5,050 ms and the playhead moves for one tick longer than the test
    asked. The scheduler's own error over the same run is nothing at all.
    """
    segments = as_segments(rows)
    end = 120_000
    answer = ask(
        scheduler,
        {
            "job": "scheduleRun",
            "segments": segments,
            "options": {"guardBandMs": 500},
            "phases": [
                {"untilWallMs": stall_at, "kind": "play", "rate": rate},
                {"untilWallMs": stall_at + stall_for, "kind": "stall"},
                {"untilWallMs": end, "kind": "play", "rate": rate},
            ],
            "seeks": [{"atWallMs": end // 2, "toMediaMs": seek_to}],
            "endWallMs": end,
            "reportEveryMs": report_every,
            "driftFactor": 1.0,
        },
    )
    one_tick_of_media = 50 * rate
    assert abs(answer["worstEstimateErrorMs"]) <= one_tick_of_media + 0.001, (
        "with no drift the estimate should follow the player, and it was out by "
        f"{answer['worstEstimateErrorMs']} ms against a bound of {one_tick_of_media} ms"
    )
    assert not answer["uncoveredAt"], answer["uncoveredAt"][:3]


def test_a_long_stall_does_not_move_the_estimate(scheduler):
    """The deterministic half of the test above, and the one that matters most.

    Thirty seconds of stall. A clock that carried on from where it was, rather than
    re-anchoring when the player stopped and started, would come out of this thirty seconds
    ahead of the playhead and draw every cover for the next half minute in the wrong place.
    """
    answer = ask(
        scheduler,
        {
            "job": "scheduleRun",
            "segments": [{"startMs": 90_000, "endMs": 93_000, "reason": "general"}],
            "options": {"guardBandMs": 500},
            "phases": [
                {"untilWallMs": 20_000, "kind": "play", "rate": 1.0},
                {"untilWallMs": 50_000, "kind": "stall"},
                {"untilWallMs": 150_000, "kind": "play", "rate": 1.0},
            ],
            "endWallMs": 150_000,
            "reportEveryMs": 400,
            "driftFactor": 1.0,
        },
    )
    assert answer["ticksInsideFlagged"] > 0, "the run never reached the flagged span"
    assert abs(answer["worstEstimateErrorMs"]) <= 50.001, (
        "the estimate ran on through a thirty second stall, and is now out by "
        f"{answer['worstEstimateErrorMs']} ms"
    )
    assert not answer["uncoveredAt"], answer["uncoveredAt"][:3]


def test_the_runner_is_driving_the_real_module(scheduler):
    """A negative control for the whole file.

    If the runner were answering from a stub, everything above would pass and mean nothing.
    This asks for something only the real schedule does: a 500 ms guard band by default, and
    a refusal for an offset past MAX_RENDITION_START_OFFSET_MS.
    """
    answer = ask(
        scheduler,
        {"job": "schedule", "segments": [{"startMs": 10_000, "endMs": 12_000}], "options": {}},
    )
    assert answer["intervals"] == [
        {
            "startMs": 9_500,
            "endMs": 12_500,
            "reason": "general",
            "sources": [{"startMs": 10_000, "endMs": 12_000}],
        }
    ]
    refused = scheduler.call(
        {
            "job": "schedule",
            "segments": [{"startMs": 10_000, "endMs": 12_000}],
            "options": {"renditionStartOffsetMs": 151},
        }
    )
    assert refused["ok"] is False
    assert "further than verify allows" in refused["error"]
