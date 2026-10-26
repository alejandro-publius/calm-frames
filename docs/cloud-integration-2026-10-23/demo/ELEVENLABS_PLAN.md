# Bounded narration plan

No generation has occurred. Produce manga and narration only after the product is finished, selected and validated, then reconcile the story with that accepted source. Missing technical inputs are a usable secure credential, API access and selection of an available built-in voice. No voice cloning, microphone recording, automatic playback or publication is part of this plan.

## Official interface verified

The official [ElevenLabs Python SDK README](https://github.com/elevenlabs/elevenlabs-python/blob/f5d53e09e35717523435cee238ac5cc7f51966fb/README.md) was read through GitHub on October 23, 2026. Its head was f5d53e09e35717523435cee238ac5cc7f51966fb. It documents ElevenLabs().text_to_speech.convert with text, voice_id, model_id and output_format, returning audio chunks. It points to the official API reference and recommends Multilingual v2 for most use cases. This confirms the interface, not pricing, a granted voice license or SDK installation. Recheck the selected SDK version and account/model pricing before a paid call.

Never call the README's play, stream, cloning or microphone examples. Write audio chunks to owned cache files. Any ELEVENLABS_API_KEY must come from a supported secure binding; it is absent in this executor. Never put its value in scripts, manifests, logs or chat.

## Approval received; production deferred

The owner approved the exact [storyboard script](STORYBOARD.md), authorized choosing a calm built-in voice and explicitly authorized an unlimited budget. The approved narration-cues.json SHA256 is recorded in timeline.json. No further script, voice-selection or budget permission is needed for that unchanged text and scope. The subsequent instruction defers media production until the product is finished. It does not accept unseen audio or a final video. Record the actual selected built-in voice ID, model and format only when available; no voice has been selected here.

Keep the job to the eight planned cues, reuse verified cached audio and perform no automatic retries. If reconciliation with the accepted product changes the words, obtain approval for the revised script. No other provider's credits are treated as an ElevenLabs balance.

## Procedure after approval

1. After product acceptance, confirm official pricing and the actual account, then calculate the expected cost for the eight cues. Verify the API destination and secure binding through supported tools. The owner's unlimited budget authorization is not a reason to add cues, retries or a new scope.
2. Pin the SDK version in a separate narration workspace. Cache key: exact text, voice ID, model ID, output format and settings. Verify hashes before reusing successful cached audio.
3. Generate one cue at a time; write a temporary file, then atomically rename. Record request ID if supplied, credits if available, exact settings, bytes and SHA256. No automatic alternate-voice or failed-request retry.
4. Measure each cue with ffprobe. It must fit its window without speed-up. If not, stop and revise wording/timing for approval. The renderer derives subtitle ends from measured audio durations and leaves intervening silence.
5. Listen to every cue for pronunciation and artifacts. Then render and review the final speech/app-audio mix, captions and full-video pacing. Signal measurements do not count as listening.

There is no narration or added music in the 70-second ambient passage. Disclose synthetic narration in the description. Publication remains a separate exact-artifact decision.
