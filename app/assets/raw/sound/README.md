# The chime

`calm-chime.mp3` is the soft cue that sounds a fixed time before a cover goes on.
It is ours, generated rather than sourced, so there is no licence to check and no
credit line to carry. Regenerate it with:

    ffmpeg -y \
      -f lavfi -i "sine=frequency=880:duration=0.9" \
      -f lavfi -i "sine=frequency=1320:duration=0.9" \
      -filter_complex "[0:a]volume=0.5[a];[1:a]volume=0.25,adelay=90|90[b];[a][b]amix=inputs=2:normalize=0,afade=t=out:st=0.15:d=0.75:curve=exp,volume=0.5,aformat=sample_rates=48000:channel_layouts=stereo[out]" \
      -map "[out]" -c:a libmp3lame -b:a 128k calm-chime.mp3

Two tones a fifth apart, the second entering 90 ms late, with an exponential fade
over three quarters of a second. It is deliberately quiet and it has no sharp
attack, because the point of it is to let a child know the picture is about to go
dark, not to startle one.

**It has never been heard on a device.** The audio path is `AudioPlayer` from
`@amazon-devices/react-native-w3cmedia`, which implements `HTMLAudioElement` and
is separate from the `VideoPlayer` the title plays through. That separation is
read from the package's own README and typings, and nothing here has played a
sound on the virtual device or on a stick.
