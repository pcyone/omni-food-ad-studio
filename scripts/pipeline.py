#!/usr/bin/env python3
"""Deterministic local stages. External research/Flow and reviews remain agent-owned."""
import argparse
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(args):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f'{args[0]} failed: {p.stderr[-1800:]}')
    return p.stdout, p.stderr


def ff(args):
    return run(['ffmpeg', '-hide_banner', '-nostdin', '-y', *args])


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path])[0])


def duration(path):
    return float(probe(path)['format']['duration'])


def stream(info, kind):
    return next((x for x in info['streams'] if x['codec_type'] == kind), {})


def rate(value):
    a, b = value.split('/')
    return float(a) / float(b) if float(b) else 0


def require(condition, message):
    if not condition:
        raise ValueError(message)


RIGHTS = ('reference_local_use', 'reference_ai_upload', 'reference_commercial',
          'model_terms', 'voice', 'likeness_brand', 'music_sound')


def init(dish, root):
    require(dish.strip(), 'Dish cannot be empty')
    require(not root.exists(), 'Project already exists; choose a new path or resume it explicitly')
    root.mkdir(parents=True)
    for name in ('source', 'references', 'prompts', 'generated', 'outputs', 'evidence'):
        (root / name).mkdir()
    save(root / 'project.json', {'dish': dish, 'duration': 40, 'fps': 24, 'created_at': datetime.now(timezone.utc).isoformat()})
    save(root / 'rights.json', {key: {'status': 'pending', 'evidence': ''} for key in RIGHTS})
    labels = ['备料腌制', '主体初熟', '辅料合炒', '出锅英雄镜头']
    save(root / 'edl.json', {'source': '', 'scenes': [
        {'id': f'{i+1:02}', 'label': label, 'ranges': [], 'frames': []}
        for i, label in enumerate(labels)]})
    save(root / 'generation.json', {
        'capabilities': {'checked_at': '', 'model_label': '', 'duration_10s': False,
                         'video_plus_five_images': False, 'evidence': ''},
        'scenes': [{'id': f'{i:02}', 'model_label': '', 'task_id': '', 'file': '', 'sha256': '',
                    'reference_video': '', 'reference_images': [], 'input_sha256': {}, 'attachments_verified': False,
                    'quality_pass': False, 'evidence': ''} for i in range(1, 5)]})
    save(root / 'review.json', {'final_sha256': '', 'visual_pass': False, 'narration_pass': False,
                              'hero_pass': False, 'evidence': '', 'reviewed_at': ''})
    for name, text in [('research.md', '# 菜谱研究与来源\n\n待研究，不是已完成记录。\n'),
                       ('narration.txt', '')]:
        (root / name).write_text(text, encoding='utf-8')
    print(root)


def validate_edl(edl, total):
    scenes = edl['scenes']
    require(len(scenes) == 4, 'Exactly four scenes are required')
    previous_end = 0
    for i, scene in enumerate(scenes, 1):
        require(scene['id'] == f'{i:02}' and scene['label'].strip(), 'Scene IDs must be 01..04 with labels')
        require(bool(scene['ranges']), 'Observe the source and fill semantic ranges first')
        output = 0
        for cut in scene['ranges']:
            start, end, seconds = (float(cut[x]) for x in ('start', 'end', 'output_seconds'))
            require(all(math.isfinite(x) for x in (start, end, seconds)), 'Non-finite EDL value')
            require(0 <= start < end <= total + .001 and seconds > 0, 'EDL range outside source')
            require(start >= previous_end - .001, 'Source chronology reversed or duplicated')
            require(.5 <= (end - start) / seconds <= 6, 'Speed outside safe .5–6 range; re-edit')
            require(abs(seconds * 24 - round(seconds * 24)) < .001, 'Output duration must be on a 24fps boundary')
            previous_end = end
            output += seconds
        require(abs(output - 10) < .001, 'Each scene must total exactly 10s')
        frames = scene['frames']
        require(len(frames) == 5, 'Select five semantic frames per scene')
        times = [float(x['second']) for x in frames]
        require(times == sorted(set(times)) and all(0 <= x < 10 for x in times), 'Frame times must be unique, ascending and inside 0..10')
        require(all(x['label'].strip() for x in frames), 'Frames need observed semantic labels')


def sheet(images, output, columns, width=180, height=320):
    inputs = [v for p in images for v in ('-i', p)]
    filters = [f'[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]' for i in range(len(images))]
    layout = '|'.join(f'{(i % columns)*width}_{(i//columns)*height}' for i in range(len(images)))
    filters += [''.join(f'[v{i}]' for i in range(len(images))) + f'xstack=inputs={len(images)}:layout={layout}:fill=black[out]']
    ff(['-v', 'error', *inputs, '-filter_complex', ';'.join(filters), '-map', '[out]', '-frames:v', '1', output])


def join_video(files, output):
    inputs = [v for p in files for v in ('-i', p)]
    graph = ''.join(f'[{i}:v:0]' for i in range(len(files))) + f'concat=n={len(files)}:v=1:a=0[v]'
    ff(['-v', 'error', *inputs, '-filter_complex', graph, '-map', '[v]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output])


def prepare(edl_path):
    root = edl_path.parent
    edl = read(edl_path)
    source = Path(edl['source']).expanduser().resolve()
    require(source.is_file(), 'Reference source does not exist')
    validate_edl(edl, duration(source))
    ff(['-v', 'error', '-xerror', '-i', source, '-f', 'null', '-'])
    out = root / 'references'
    require(not source.is_relative_to(out.resolve()), 'Source must not be inside the generated reference directory')
    out.mkdir(exist_ok=True)
    scenes, images = [], []
    for scene in edl['scenes']:
        folder = out / f"scene-{scene['id']}"
        folder.mkdir(exist_ok=True)
        cuts = []
        for i, cut in enumerate(scene['ranges']):
            seconds = cut['output_seconds']
            speed = (cut['end'] - cut['start']) / seconds
            part = folder / f'cut-{i+1:02}.mp4'
            vf = f'setpts=(PTS-STARTPTS)/{speed},fps=24,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1'
            ff(['-v', 'error', '-ss', cut['start'], '-t', cut['end']-cut['start'], '-i', source,
                '-an', '-vf', vf, '-frames:v', round(seconds*24), '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', part])
            cuts.append(part)
        video = out / f"scene-{scene['id']}.mp4"
        join_video(cuts, video)
        require(abs(duration(video)-10) <= 1/24, 'Reference scene duration failed')
        scenes.append(video)
        for i, frame in enumerate(scene['frames'], 1):
            p = folder / f'{i:02}.jpg'
            ff(['-v', 'error', '-ss', frame['second'], '-i', video, '-frames:v', '1', '-q:v', '2', p])
            images.append(p)
    join_video(scenes, out / 'reference-40s.mp4')
    sheet(images, out / '20张参考检查.jpg', 5)
    save(out / 'reference-manifest.json', {'source': str(source), 'source_sha256': sha(source),
        'edl': edl, 'reference_duration': duration(out/'reference-40s.mp4'),
        'scenes': [{'file': str(p), 'sha256': sha(p), 'duration': duration(p)} for p in scenes],
        'images': [{'file': str(p), 'sha256': sha(p)} for p in images], 'manual_review': 'pending'})
    print(out)


def evidence_confirmed(item):
    return item.get('status') == 'confirmed' and bool(str(item.get('evidence', '')).strip())


def generation_errors(root, generation, rights):
    errors = []
    for key in ('reference_local_use', 'reference_ai_upload'):
        if not evidence_confirmed(rights.get(key, {})):
            errors.append(f'rights.{key} unresolved')
    cap = generation.get('capabilities', {})
    if not (cap.get('video_plus_five_images') is True and cap.get('duration_10s') is True
            and cap.get('evidence') and cap.get('checked_at') and 'omni' in cap.get('model_label', '').lower()
            and '1.1' in cap.get('model_label', '')):
        errors.append('Current Omni 1.1 combined-reference capability evidence missing')
    for i, scene in enumerate(generation.get('scenes', []), 1):
        if not (scene.get('id') == f'{i:02}' and scene.get('task_id') and scene.get('evidence')
                and scene.get('attachments_verified') is True and scene.get('quality_pass') is True
                and 'omni' in scene.get('model_label', '').lower() and '1.1' in scene.get('model_label', '')):
            errors.append(f'Scene {i} generation/quality evidence incomplete')
        refs = [scene.get('reference_video', ''), *scene.get('reference_images', [])]
        if len(refs) != 6 or len(set(refs)) != 6 or any(not x or not Path(x).is_file() for x in refs):
            errors.append(f'Scene {i} needs one video and five existing image references')
        elif any(scene.get('input_sha256', {}).get(str(x)) != sha(x) for x in refs):
            errors.append(f'Scene {i} input hashes missing or changed')
        p = Path(scene.get('file', ''))
        if not p.is_file() or sha(p) != scene.get('sha256'):
            errors.append(f'Scene {i} output hash missing or changed')
    if len(generation.get('scenes', [])) != 4:
        errors.append('Exactly four generation records required')
    return errors


def voice_tempo(seconds):
    tempo = seconds / 39
    require(.88 <= tempo <= 1.18, f'Voice {seconds:.3f}s requires tempo {tempo:.3f}; revise narration and synthesize again')
    return tempo


def finish(root, voice, local_test=False, hero=38, ambient=.12):
    require(30 <= hero < 39.95, 'Select hero from the final scene')
    require(0 <= ambient <= .3, 'Ambient gain must be 0..0.3')
    generation, rights = read(root/'generation.json'), read(root/'rights.json')
    errors = generation_errors(root, generation, rights)
    require(local_test or not errors, '\n'.join(errors))
    scenes = generation['scenes']
    require(len(scenes) == 4, 'Need four scene files, even for local tests')
    clips = [Path(s['file']).resolve() for s in scenes]
    infos = [probe(p) for p in clips]
    for i, info in enumerate(infos):
        v = stream(info, 'video')
        require(abs(float(v.get('duration', info['format']['duration']))-10) <= 1/24, f'Scene {i+1} must be 10 seconds')
        require(abs(v['width']/v['height']-9/16) < .005, f'Scene {i+1} must be vertical 9:16; regenerate, do not crop')
    tempo = voice_tempo(duration(voice))
    out = root/'outputs'
    out.mkdir(exist_ok=True)
    fitted = out/'voice-fitted.wav'
    ff(['-v', 'error', '-i', voice, '-af', f'atempo={tempo:.9f},loudnorm=I=-16:LRA=8:TP=-1.5', '-ar', '48000', '-ac', '2', fitted])
    # atempo can differ by a few samples. Reserve the entire source waveform, not a guessed last word.
    require(duration(fitted) <= 39.04, 'Fitted narration exceeds its protected window')
    padded = out/'voice-timeline.wav'
    ff(['-v', 'error', '-i', fitted, '-af', 'adelay=200|200,apad,atrim=duration=40', '-ar', '48000', '-ac', '2', padded])
    inputs = [x for p in clips for x in ('-i', p)] + ['-i', padded]
    filters = []
    for i, info in enumerate(infos):
        filters.append(f'[{i}:v]scale=1080:1920,fps=24,setsar=1,setpts=PTS-STARTPTS[v{i}]')
        if stream(info, 'audio'):
            filters.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,apad,atrim=duration=10,volume={ambient}[a{i}]')
        else:
            filters.append(f'anullsrc=r=48000:cl=stereo,atrim=duration=10[a{i}]')
    filters.append(''.join(f'[v{i}][a{i}]' for i in range(4)) + 'concat=n=4:v=1:a=1[v][amb]')
    filters.append('[amb][4:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:LRA=8:TP=-1.5[a]')
    final = out/'final.mp4'
    ff(['-v', 'error', *inputs, '-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
        '-t', '40', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', final])
    save(out/'render.json', {'local_test': local_test, 'generation_errors': errors, 'final_sha256': sha(final),
        'generation_manifest_sha256': sha(root/'generation.json'),
        'source_clips': [{'path': str(p), 'sha256': sha(p), 'width': stream(info,'video')['width'],
                          'height': stream(info,'video')['height']} for p, info in zip(clips, infos)],
        'upscaled': any(stream(x,'video')['height'] < 1920 for x in infos),
        'voice_raw_sha256': sha(voice), 'voice_raw_duration': duration(voice), 'tempo': tempo,
        'fitted_duration': duration(fitted), 'voice_delay': .2, 'voice_tail_not_trimmed': True,
        'narration_fade_out': False, 'ambient_gain': ambient, 'hero_second': hero})
    verify(root)


def last_sound(path):
    _, log = ff(['-v', 'info', '-i', path, '-af', 'silencedetect=noise=-50dB:d=0.1', '-f', 'null', '-'])
    total = duration(path)
    starts = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', log)]
    return starts[-1] if starts and ends and abs(ends[-1]-total) < .06 else total


def verify(root):
    out, final = root/'outputs', root/'outputs/final.mp4'
    render = read(out/'render.json')
    require(render['final_sha256'] == sha(final), 'Final changed since render; provenance invalid')
    info = probe(final)
    v, a = stream(info, 'video'), stream(info, 'audio')
    ff(['-v', 'error', '-xerror', '-i', final, '-f', 'null', '-'])
    _, blacklog = ff(['-v', 'info', '-i', final, '-vf', 'blackdetect=d=0.5:pix_th=0.10', '-an', '-f', 'null', '-'])
    black = [float(x) for x in re.findall(r'black_duration:([0-9.]+)', blacklog)]
    _, loudlog = ff(['-v', 'info', '-i', final, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json', '-vn', '-f', 'null', '-'])
    match = re.search(r'\{\s*"input_i"[\s\S]*?\}', loudlog)
    require(match is not None, 'Loudness measurement missing')
    loudness = json.loads(match.group())
    tail = 40 - last_sound(out/'voice-timeline.wav')
    points = [1, 5, 9+23/24, 10, 15, 19+23/24, 20, 25, 29+23/24, 30, 35, 38, 39.5]
    frames = out/'qa-frames'
    frames.mkdir(exist_ok=True)
    images = []
    for i, second in enumerate(points):
        p = frames/f'{i+1:02}-{second:.3f}s.jpg'
        ff(['-v', 'error', '-ss', second, '-i', final, '-frames:v', '1', '-q:v', '2', p])
        images.append(p)
    sheet(images, out/'关键帧检查.jpg', 5)
    ff(['-v', 'error', '-ss', render['hero_second'], '-i', final, '-frames:v', '1', '-q:v', '2', out/'封面.jpg'])
    ff(['-v', 'error', '-ss', '34', '-i', final, '-vn', '-c:a', 'pcm_s16le', out/'结尾6秒.wav'])
    checks = {
        'duration_40s': abs(float(info['format']['duration'])-40) <= 1/24,
        'dimensions': (v.get('width'),v.get('height')) == (1080,1920),
        'fps_24': abs(rate(v.get('avg_frame_rate','0/1'))-24) < .001,
        'frames_960': int(v.get('nb_frames',0)) == 960,
        'h264_yuv420p': v.get('codec_name')=='h264' and v.get('pix_fmt')=='yuv420p',
        'aac_48k_stereo': a.get('codec_name')=='aac' and a.get('sample_rate')=='48000' and a.get('channels')==2,
        'full_decode': True, 'no_black_over_0_5s': not black,
        'voice_tail_at_least_0_8s': tail >= .8 - 1/24,
        'audible_loudness': -18 <= float(loudness['input_i']) <= -14,
        'true_peak_safe': float(loudness['input_tp']) <= -.8,
    }
    review, rights = read(root/'review.json'), read(root/'rights.json')
    reviewed = review.get('final_sha256') == sha(final) and bool(review.get('evidence')) and bool(review.get('reviewed_at'))
    creative = reviewed and all(review.get(k) is True for k in ('visual_pass','narration_pass','hero_pass'))
    right_ok = all(evidence_confirmed(rights.get(k, {})) for k in RIGHTS)
    gen_errors = generation_errors(root, read(root/'generation.json'), rights)
    if render.get('generation_manifest_sha256') != sha(root/'generation.json'):
        gen_errors.append('Generation manifest changed after render or render evidence predates hash binding')
    technical = all(checks.values())
    report = {'measured_at': datetime.now(timezone.utc).isoformat(), 'final_sha256': sha(final),
        'checks': checks, 'technical_pass': technical, 'creative_pass': bool(creative),
        'commercial_ready': bool(technical and creative and right_ok and not gen_errors and not render['local_test']),
        'commercial_note': 'Workflow evidence review only; not a legal guarantee.',
        'rights_confirmed': right_ok, 'generation_errors': gen_errors, 'render': render,
        'duration': float(info['format']['duration']), 'voice_tail_seconds': tail,
        'loudness': loudness, 'black_segments': black, 'keyframe_seconds': points,
        'manual_review': review, 'ffprobe': info}
    save(out/'verification.json', report)
    print(json.dumps({k:report[k] for k in ('technical_pass','creative_pass','commercial_ready')}, ensure_ascii=False))
    require(technical, 'Technical QA failed; inspect verification.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('dish'); p.add_argument('root', type=Path)
    p = sub.add_parser('prepare'); p.add_argument('edl', type=Path)
    p = sub.add_parser('finish'); p.add_argument('root', type=Path); p.add_argument('--voice', type=Path, required=True)
    p.add_argument('--local-test', action='store_true'); p.add_argument('--hero-second', type=float, default=38)
    p.add_argument('--ambient', type=float, default=.12)
    p = sub.add_parser('verify'); p.add_argument('root', type=Path)
    args = parser.parse_args()
    if args.command == 'init': init(args.dish, args.root.expanduser().resolve())
    elif args.command == 'prepare': prepare(args.edl.expanduser().resolve())
    elif args.command == 'finish': finish(args.root.expanduser().resolve(), args.voice.expanduser().resolve(), args.local_test, args.hero_second, args.ambient)
    else: verify(args.root.expanduser().resolve())


if __name__ == '__main__':
    main()
