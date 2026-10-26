# Independent finish-pass review

Reviewer: /root/finish_review, read-only; baseline 7f0567f, reviewed the current finish-pass diff before build.

Finding resolved: disabling BufferingWindow live regions exposed global same-text announcement deduplication. A second separate waiting episode could be silent. Each revealed episode now uses one explicit announcement with force:true and queue:false. The regression exercises the accessibility API across two episodes. Focused checks pass.

No remaining blocking lifecycle, focus or safety regression identified. The media-clock monitor is read-only and resets for pause, seeking, rate changes and discontinuities. End handling uses the existing idempotent teardown and retains its fallback delay.

Limitation: historical timeupdate-event replay validates the classifier against recorded evidence. Production polls currentTime once a second. Replay does not establish native status display or audio behavior. Native verification and visual/audio acceptance are separate.
