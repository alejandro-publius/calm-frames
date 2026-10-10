"""Assemble real simulator captures with disclosed editorial stills and TTS.

Run from the repository root after capturing the sources listed below.
No app frames are generated or altered beyond scaling and a footer caption.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/submission'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
# Source, start offset, duration, English narration. PNGs are disclosed stills.
SHOTS = [
 ('docs/brand/firetv-app-icon-1280x720.png', 0, 6,
  'Calm Frames. A calmer way to watch.'),
 ('.logs/native-final-shelf.png', 0, 10,
  'This accessibility prototype is running on the Vega Virtual Device. Its shelf contains checked, packaged videos.'),
 ('.logs/native-practice-before-seek.png', 0, 12,
  'Harbor is original, non-flashing media. This practice title uses two scheduled holds to demonstrate scene continuity. The intervals are synthetic, not detected flashing.'),
 ('.logs/native-reviewed-harbor.mp4', 2, 25,
  'Watch the practice holds. The recorded tone and English captions continue while a calm scene is held.'),
 ('.logs/native-guarded-transport.mp4', 5, 20,
  'Here the remote seeks forward and backward, pauses, and resumes. The player uses an opaque fallback when playback is disrupted. This is behavior, not a screen timing measurement.'),
 ('.logs/native-credits-return.png', 0, 8,
  'A parent PIN protects settings. Wrong entries stay locked, and a partial entry can be corrected with Delete.'),
 ('.logs/native-extra-selected2.png', 0, 10,
  'Parents choose Standard, Broadcast, or Extra cautious. Stricter choices cannot relax the household floor. Each prepared preset was played in the simulator.'),
 ('.logs/native-kid-history-visible.png', 0, 12,
  'Room settings, the selected profile, and the chime switch survive restart. Practice holds are excluded from exposure history. Actual cover history is kept in memory.'),
 ('.logs/native-broadcast-play.mp4', 3, 19,
  'This separate Harbor title went through real local preparation, with no synthetic detector intervals. The app plays the verified rendition compiled into its catalog. This source had no detected flashing.'),
 ('build/submission/status-card.png', 0, 18,
  'The saved AWS run published a signed title, but this app consumes its local library. Detection can miss flashing. Calm Frames is not a medical device. Dependency security findings remain open.'),
 ('docs/brand/firetv-app-icon-1280x720.png', 0, 6,
  'Calm Frames. A calmer way to watch.'),
]


def run(args):
    subprocess.run(args, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'json', str(path)]))['format']['duration']


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    card = Image.new('RGB', (1920,1080), '#1d4b58')
    draw = ImageDraw.Draw(card)
    draw.text((115,115), 'Prototype status', font=ImageFont.truetype(FONT,76), fill='#f4ead3')
    lines = ['Prepared, compiled local library', 'AWS publication is a separate demonstrated pipeline',
             'Detection can miss flashing', 'No medical outcome or physical-TV timing claim',
             'Dependency security audit: unresolved findings']
    for i, line in enumerate(lines):
        draw.text((115,290+i*110), line, font=ImageFont.truetype(FONT,46), fill='#f4ead3')
    card.save(OUT/'status-card.png')
    manifest=[]
    captions=[]
    cursor=0
    for i,(source,start,seconds,narration) in enumerate(SHOTS):
        source_path=ROOT/source
        assert source_path.is_file(), source
        voice=OUT/f'voice-{i:02}.aiff'
        textfile=OUT/f'voice-{i:02}.txt'
        textfile.write_text(narration+'\n')
        run(['say','-v','Samantha','-r','165','-o',str(voice),'-f',str(textfile)])
        voice_seconds=float(probe(voice))
        if voice_seconds > seconds - 0.3:
            seconds=round(voice_seconds+0.7,1)
        overlay=Image.new('RGBA',(1920,1080),(0,0,0,0))
        d=ImageDraw.Draw(overlay)
        d.rectangle((0,944,1920,1080),fill=(12,32,39,255))
        label='Vega Virtual Device | Actual capture' if source.startswith('.logs') else 'Calm Frames | Editorial card'
        d.text((55,952),label, font=ImageFont.truetype(FONT,23),fill='#e6ab55')
        # The subtitle footer occupies only the capture's black lower margin.
        lines=textwrap.wrap(narration,width=110)
        f=ImageFont.truetype(FONT,30 if len(lines)>2 else 34)
        for j,line in enumerate(lines):
            d.text((55,987+j*29),line,font=f,fill='#f4ead3')
        overlay_path=OUT/f'footer-{i:02}.png'
        overlay.save(overlay_path)
        args=['ffmpeg','-v','error','-y']
        still=source_path.suffix=='.png'
        if still: args+=['-loop','1','-framerate','30','-i',str(source_path)]
        else: args+=['-ss',str(start),'-i',str(source_path)]
        args+=['-loop','1','-i',str(overlay_path),'-i',str(voice)]
        graph='[0:v]scale=1920:1080,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=30[v];[v][1:v]overlay=0:0:shortest=1[outv];'
        if still:
            graph+='[2:a]aresample=48000,apad[outa]'
        else:
            graph+='[0:a]aresample=48000,volume=6.3,apad[native];[2:a]aresample=48000,apad[voice];[native][voice]amix=inputs=2:normalize=0[outa]'
        dest=OUT/f'part-{i:02}.mp4'
        args+=['-filter_complex',graph,'-map','[outv]','-map','[outa]','-t',str(seconds),
               '-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',str(dest)]
        run(args)
        manifest.append({'source':source,'source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
                         'source_start_seconds':start,'output_start_seconds':cursor,'duration_seconds':seconds,
                         'still':still,'narration':narration,'narration_voice':'macOS Samantha TTS',
                         'native_audio_gain_db':0 if still else 15.99})
        captions.append(f'{i+1}\n{stamp(cursor)} --> {stamp(cursor+seconds)}\n{narration}\n')
        cursor+=seconds
        print(f'Encoded shot {i+1}: {seconds}s',flush=True)
    assert cursor <179, cursor
    concat=OUT/'parts.txt'
    concat.write_text(''.join(f"file 'part-{i:02}.mp4'\n" for i in range(len(SHOTS))))
    final=OUT/'Calm-Frames-demo-English.mp4'
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)])
    (OUT/'Calm-Frames-demo-English.srt').write_text('\n'.join(captions))
    result={'video':str(final.relative_to(ROOT)), 'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
            'duration_seconds':float(probe(final)), 'language':'English', 'narration':'macOS Samantha synthetic narration',
            'footage':'Actual Vega Virtual Device recordings and disclosed still captures; editorial brand/status cards',
            'edits':'Cuts, scaling, constant-frame-rate encoding, footer subtitles, narration and native audio gain. No generated app footage.',
            'shots':manifest}
    (ROOT/'results/demo_manifest_2026-10-10.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='shots'}))

if __name__=='__main__':
    main()
