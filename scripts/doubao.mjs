#!/usr/bin/env node
// One request, continuous narration. No credentials or response bodies in logs.
import {readFileSync, writeFileSync, existsSync, mkdirSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';

const args = {};
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i];
  if (key === '--help') {
    console.log('node doubao.mjs --script narration.txt --out voice.wav [--env private.env]');
    process.exit(0);
  }
  if (!['--script', '--out', '--env'].includes(key) || !process.argv[i+1]) throw new Error('Invalid arguments; use --help');
  args[key.slice(2)] = process.argv[i+1];
}
if (!args.script || !args.out) throw new Error('Use --script and --out');
const envFile = args.env || process.env.DOUBAO_TTS_ENV_FILE;
if (envFile) {
  for (const raw of readFileSync(envFile, 'utf8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const at = line.indexOf('=');
    if (at <= 0) continue;
    const key = line.slice(0, at).trim();
    if (!key.startsWith('DOUBAO_TTS_')) continue;
    process.env[key] ||= line.slice(at+1).trim().replace(/^['"]|['"]$/g, '');
  }
}
const required = key => {
  if (!process.env[key]?.trim()) throw new Error(`${key} is not configured`);
  return process.env[key].trim();
};
const output = resolve(args.out);
if (existsSync(output)) throw new Error('Output already exists; choose a versioned filename to avoid another billed request');
const text = readFileSync(args.script, 'utf8').trim();
if (!text || text.length > 2500) throw new Error('Narration is empty or too long');
const speechRate = Number(process.env.DOUBAO_TTS_SPEECH_RATE ?? -2);
if (!Number.isFinite(speechRate)) throw new Error('Invalid speech rate');
const request = {
  text, speaker: required('DOUBAO_TTS_SPEAKER'),
  audio_params: {format:'pcm', sample_rate:24000, speech_rate:speechRate, loudness_rate:0},
  additions: JSON.stringify({explicit_language:'zh', enable_language_detector:true, silence_duration:120}),
};
if (process.env.DOUBAO_TTS_MODEL?.trim()) request.model = process.env.DOUBAO_TTS_MODEL.trim();
const response = await fetch('https://openspeech.bytedance.com/api/v3/tts/unidirectional', {
  method:'POST', signal: AbortSignal.timeout(180000),
  headers: {'Content-Type':'application/json', 'X-Api-Key':required('DOUBAO_TTS_API_KEY'),
    'X-Api-Resource-Id':required('DOUBAO_TTS_RESOURCE_ID'), 'X-Api-Request-Id':randomUUID()},
  body: JSON.stringify({user:{uid:`food-ad-${randomUUID()}`}, req_params:request}),
});
if (!response.ok) throw new Error(`Doubao HTTP ${response.status}; check task/config before retrying`);
const raw = await response.text();
const items = [];
let start = -1, depth = 0, quoted = false, escaped = false;
for (let i=0; i<raw.length; i++) {
  const ch = raw[i];
  if (quoted) {
    if (escaped) escaped=false;
    else if (ch==='\\') escaped=true;
    else if (ch==='"') quoted=false;
  } else if (ch==='"') quoted=true;
  else if (ch==='{') {if (depth++===0) start=i;}
  else if (ch==='}' && --depth===0 && start>=0) items.push(JSON.parse(raw.slice(start,i+1)));
}
if (!items.some(x=>x.code===20000000) || items.some(x=>typeof x.code==='number' && ![0,20000000].includes(x.code))) {
  throw new Error('Doubao stream did not complete successfully; no partial speech accepted');
}
const audio=Buffer.concat(items.filter(x=>x.code===0 && typeof x.data==='string').map(x=>Buffer.from(x.data,'base64')));
if (!audio.length) throw new Error('Doubao returned no audio');
mkdirSync(dirname(output), {recursive:true});
const pcm=`${output}.raw.pcm`;
writeFileSync(pcm,audio,{flag:'wx'});
execFileSync('ffmpeg',['-hide_banner','-nostdin','-v','error','-n','-f','s16le','-ar','24000','-ac','1','-i',pcm,
  '-af','silenceremove=start_periods=1:start_duration=0.04:start_threshold=-50dB:start_silence=0.03',
  '-ar','48000','-ac','1','-c:a','pcm_s16le',output]);
console.log(JSON.stringify({output, continuous_request:true, tail_trimmed:false}));
