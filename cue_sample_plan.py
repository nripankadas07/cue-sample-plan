"""Partition captured CUE/WAVE audio into exact sample-frame track and gap ranges."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import sys
import wave
from collections import Counter
from pathlib import Path

MAX_CUE=65536
MAX_WAVE=64*1024*1024

def timestamp(value):
    m=re.fullmatch(r'([0-9]{2,3}):([0-9]{2}):([0-9]{2})',value)
    if not m or int(m[2])>=60 or int(m[3])>=75:raise ValueError('CUE timestamp must be MM:SS:FF, seconds<60 and frames<75')
    return (int(m[1])*60+int(m[2]))*75+int(m[3])

def parse_cue(text):
    if len(text.encode('utf-8'))>MAX_CUE or '\0' in text:raise ValueError('CUE exceeds 64 KiB or contains NUL')
    files=[];track=None;seen=set();expected=1;ignored=Counter()
    for line in text.splitlines():
        line=line.strip()
        if not line:continue
        tag=line.split()[0]
        if tag=='FILE':
            m=re.fullmatch(r'FILE\s+"([^"\r\n]+)"\s+WAVE',line)
            if not m or (track is not None and 1 not in track['indices']):raise ValueError('quoted WAVE FILE required after a complete track')
            name=m[1]
            if not name.isprintable() or name in ('.','..') or any(c in name for c in '/\\:') or name in seen or len(name)>200 or len(files)>=16:raise ValueError('distinct local basenames only; no traversal, drives or repeated FILE blocks')
            files.append({'name':name,'tracks':[]});seen.add(name);track=None
        elif tag=='TRACK':
            m=re.fullmatch(r'TRACK\s+([0-9]{2})\s+AUDIO',line)
            if not m or not files or (track is not None and 1 not in track['indices']) or int(m[1])!=expected:raise ValueError('sequential AUDIO tracks 01..99 required')
            track={'track':expected,'indices':{}};files[-1]['tracks'].append(track);expected+=1
        elif tag=='INDEX':
            m=re.fullmatch(r'INDEX\s+(00|01)\s+(\S+)',line)
            if not m or track is None:raise ValueError('only track INDEX00/01 supported')
            idx=int(m[1])
            if idx in track['indices'] or (idx==0 and 1 in track['indices']):raise ValueError('duplicate or out-of-order index')
            track['indices'][idx]=timestamp(m[2])
        elif tag in ('REM','TITLE','PERFORMER','SONGWRITER','ISRC','CATALOG'):ignored[tag]+=1
        else:raise ValueError('unsupported CUE directive '+tag+' (no synthetic PREGAP/POSTGAP)')
    if not files or any(not f['tracks'] or any(1 not in t['indices'] for t in f['tracks']) for f in files):raise ValueError('every file needs complete tracks')
    return files,dict(sorted(ignored.items()))

def wave_info(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_WAVE:raise ValueError('regular non-symlink WAVE file <=64 MiB required')
    with path.open('rb') as f:raw=f.read(MAX_WAVE+1)
    if len(raw)>MAX_WAVE or len(raw)<12 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE' or struct.unpack_from('<I',raw,4)[0]!=len(raw)-8:raise ValueError('exact little-endian RIFF/WAVE container required')
    pos=12;fmt=None;data=None;ignored=Counter()
    while pos<len(raw):
        if pos+8>len(raw):raise ValueError('truncated RIFF chunk header')
        tag=raw[pos:pos+4];size=struct.unpack_from('<I',raw,pos+4)[0];start=pos+8;end=start+size
        if end+(size%2)>len(raw):raise ValueError('truncated RIFF chunk data/padding')
        if tag==b'fmt ':
            if fmt is not None or size not in (16,18) or (size==18 and raw[start+16:start+18]!=b'\0\0'):raise ValueError('single plain fmt chunk required')
            fmt=struct.unpack_from('<HHIIHH',raw,start)
        elif tag==b'data':
            if data is not None:raise ValueError('multiple data chunks unsupported')
            data=(start,size)
        else:ignored[tag.decode('ascii',errors='replace')]+=1
        pos=end+size%2
    if fmt is None or data is None:raise ValueError('fmt and data chunks required')
    encoding,channels,rate,byte_rate,align,bits=fmt
    if not 1<=channels<=8 or not 8000<=rate<=192000 or encoding not in (1,3):raise ValueError('PCM/IEEE-float, 1..8 channels and sample rate8000..192000 required')
    if bits not in ((8,16,24,32) if encoding==1 else (32,64)) or align!=channels*bits//8 or byte_rate!=rate*align or not data[1] or data[1]%align:raise ValueError('invalid sample format, alignment or data length')
    return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'encoding':'PCM' if encoding==1 else 'IEEE_FLOAT','channels':channels,'sample_rate':rate,'bits_per_sample':bits,'block_align':align,'data_offset':data[0],'sample_frames':data[1]//align,'ignored_chunks':dict(sorted(ignored.items()))}

def plan(cue_path):
    path=Path(cue_path)
    with path.open('rb') as f:raw=f.read(MAX_CUE+1)
    if len(raw)>MAX_CUE:raise ValueError('CUE exceeds 64 KiB')
    files,ignored=parse_cue(raw.decode('utf-8-sig'))
    source_paths=[path.parent/f['name'] for f in files]
    if any(p.is_symlink() or not p.is_file() for p in source_paths):raise ValueError('all referenced sources must be existing non-symlink local files')
    if sum(p.stat().st_size for p in source_paths)>128*1024*1024:raise ValueError('aggregate WAVE bytes exceed128MiB')
    results=[];findings=[]
    for file,source in zip(files,source_paths):
        info=wave_info(source);rate=info['sample_rate'];total=info['sample_frames'];tracks=file['tracks'];indices=[]
        for track in tracks:
            converted={}
            for idx,frame in track['indices'].items():
                n=frame*rate
                if n%75:raise ValueError('CUE index is not an exact sample-frame boundary at this sample rate')
                converted[idx]=n//75
            if 0 in converted and converted[0]>converted[1]:raise ValueError('INDEX00 follows INDEX01')
            if not 0<=converted[1]<total:raise ValueError('track start outside audio data')
            indices.append(converted)
        spans=[]
        def add(kind,track,a,b):
            if b<a:raise ValueError('overlapping or decreasing CUE boundaries')
            if a==b:return
            spans.append({'kind':kind,'track':track,'start_sample_frame':a,'end_sample_frame_exclusive':b,'sample_frames':b-a,
                'start_file_byte':info['data_offset']+a*info['block_align'],'end_file_byte_exclusive':info['data_offset']+b*info['block_align']})
        first=indices[0].get(0,indices[0][1])
        if first:
            add('unassigned_leading_audio',None,0,first);findings.append({'file':file['name'],'reason':'unassigned_leading_audio','sample_frames':first})
        for i,track in enumerate(tracks):
            idx=indices[i];start=idx[1]
            if 0 in idx:add('recorded_pregap',track['track'],idx[0],start)
            end=indices[i+1].get(0,indices[i+1][1]) if i+1<len(tracks) else total
            if end<=start:raise ValueError('each track requires a positive nonoverlapping audio interval')
            add('track_audio',track['track'],start,end)
        cursor=0
        for span in spans:
            if span['start_sample_frame']!=cursor:raise ValueError('internal partition is not contiguous')
            cursor=span['end_sample_frame_exclusive']
        if cursor!=total:raise ValueError('internal partition did not cover all sample frames')
        results.append({'file':file['name'],'wave':info,'partitions':spans})
    return {'cue_sha256':hashlib.sha256(raw).hexdigest(),'files':results,'ignored_metadata':ignored,'findings':findings,
        'scope':'Plan only, no audio copying or encoder execution. Sample frames include all channels. Recorded INDEX00 gaps are separate; synthetic gaps unsupported. CUE indices must land exactly on WAVE sample frames. No compressed, RF64, big-endian or extensible WAVE support; no audio-content/quality claim.'}

def make_example(directory):
    d=Path(directory);d.mkdir()
    with wave.open(str(d/'example.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100);w.writeframes(b'\0\0'*(4*44100))
    (d/'example.cue').write_text('FILE "example.wav" WAVE\n  TRACK 01 AUDIO\n    INDEX 01 00:00:00\n  TRACK 02 AUDIO\n    INDEX 00 00:01:00\n    INDEX 01 00:02:00\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cue',nargs='?');p.add_argument('--make-example',metavar='NEW_DIRECTORY');a=p.parse_args()
    try:
        if a.make_example:
            if a.cue:raise ValueError('example generation cannot be combined with a source')
            make_example(a.make_example);print(json.dumps({'example_directory':a.make_example,'audio':'invented silence'}));return 0
        if not a.cue:raise ValueError('CUE path required')
        r=plan(a.cue);print(json.dumps(r,sort_keys=True,indent=2));return int(bool(r['findings']))
    except (ValueError,OSError,UnicodeError,struct.error,wave.Error,OverflowError) as e:
        print(json.dumps({'error':str(e)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
