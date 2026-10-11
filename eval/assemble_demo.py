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
OUT = ROOT / 'build/submission-redesign'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
# Source, start offset, duration, English narration. PNGs are disclosed stills.
SHOTS = [
 ('docs/brand/firetv-app-icon-1280x720.png', 0, 6,
  'Calm Frames. A calmer way to watch.'),
 ('.logs/redesign-final-library.png', 0, 10,
  'Calm Frames is running on the Vega Virtual Device. This redesigned library contains the checked videos packaged with the app.'),
 ('.logs/redesign-final-details.png', 0, 12,
  'Harbor is original, non-flashing media. The scene hold demo adds two scheduled holds. These are examples, not detected flashing.'),
 ('.logs/redesign-final-harbor.mp4', 2, 26,
  'Watch the scheduled holds. The recorded tone and English captions continue while the picture holds a calm scene.'),
 ('.logs/redesign-final-transport.mp4', 2, 22,
  'The remote seeks, pauses, and resumes. Interrupted playback uses an opaque cover. This demonstrates behavior, not physical screen timing.'),
 ('.logs/redesign-final-pin.png', 0, 9,
  'A PIN protects parental controls. Incorrect entries stay locked, and Delete corrects a partial entry.'),
 ('.logs/redesign-final-parent.png', 0, 12,
  'Parents choose Standard, Broadcast, or Extra cautious. Each choice was tested in Vega. A child cannot relax the settings chosen for everyone.'),
 ('.logs/redesign-final-history.png', 0, 12,
  'Settings survive restart. Scheduled demo holds are excluded from exposure history. Actual cover history is not saved across app restarts.'),
 ('.logs/redesign-final-prepared.mp4', 2, 21,
  'This separate Harbor title uses real local preparation without the demonstration holds. The app plays its checked, packaged rendition. The source had no detected flashing.'),
 ('build/submission-redesign/status-card.png', 0, 20,
  'The saved AWS run published a signed title. The app uses its local library. Detection can miss flashing. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device.'),
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
    card = Image.new('RGB', (1920,1080), '#102F3A')
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
        label=('Vega Virtual Device | Actual still capture' if source_path.suffix=='.png' else 'Vega Virtual Device | Actual video capture') if source.startswith('.logs') else 'Calm Frames | Editorial card'
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
    result={'capture_source_commit':'cba1a29f300b17b11cfaaf723c6f34d4d8bdf190',
            'capture_package_sha256':'12f757db105ed2aa15d19017963ec63748917e2c4141e0026120390b3be6ecd1',
            'video':str(final.relative_to(ROOT)), 'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
            'duration_seconds':float(probe(final)), 'language':'English', 'narration':'macOS Samantha synthetic narration',
            'footage':'Actual Vega Virtual Device recordings and disclosed still captures; editorial brand/status cards',
            'edits':'Cuts, scaling, constant-frame-rate encoding, footer subtitles, narration and native audio gain. No generated app footage.',
            'shots':manifest}
    (ROOT/'results/redesign_demo_manifest_2026-10-10.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='shots'}))

if __name__=='__main__':
    main()
