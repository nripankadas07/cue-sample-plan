import pathlib,subprocess,sys,tempfile,json,hashlib,shutil
PYTHON=pathlib.Path(sys.argv[1]).absolute()
SOURCE=pathlib.Path(__file__).absolute().parent
COMMAND=PYTHON.parent/"cue-sample-plan"
with tempfile.TemporaryDirectory() as td:
 work=pathlib.Path(td)
 def run(args,code=0):
  p=subprocess.run([str(COMMAND),*map(str,args)],cwd=work,text=True,capture_output=True,timeout=20)
  assert p.returncode==code,(args,p.returncode,p.stdout,p.stderr)
  if code==2:
   assert not p.stdout and p.stderr,(p.stdout,p.stderr)
   return None
  return json.loads(p.stdout)
 help_result=subprocess.run([str(COMMAND),"--help"],cwd=work,capture_output=True,text=True,timeout=10)
 assert help_result.returncode==0 and "usage:" in help_result.stdout
 installed=subprocess.run([str(PYTHON),"-I","-c","import cue_sample_plan,pathlib,hashlib;print(hashlib.sha256(pathlib.Path(cue_sample_plan.__file__).read_bytes()).hexdigest())"],cwd=work,capture_output=True,text=True,check=True).stdout.strip()
 assert installed==hashlib.sha256((SOURCE/"cue_sample_plan.py").read_bytes()).hexdigest()
 for p in SOURCE.glob("example.*"):shutil.copyfile(p,work/p.name)
 run(['--make-example','fixture'])
 cue=work/'fixture/example.cue';wav=work/'fixture/example.wav';before=hashlib.sha256(wav.read_bytes()).hexdigest()
 r=run([cue]);spans=r['files'][0]['partitions']
 assert [(p['start_sample_frame'],p['end_sample_frame_exclusive']) for p in spans]==[(0,44100),(44100,88200),(88200,176400)]
 assert [p['kind'] for p in spans]==['track_audio','recorded_pregap','track_audio']
 assert hashlib.sha256(wav.read_bytes()).hexdigest()==before==r['files'][0]['wave']['sha256']
 original=cue.read_text();cue.write_text(original.replace('INDEX 01 00:00:00','INDEX 01 00:00:01'))
 assert run([cue],1)['findings'][0]['reason']=='unassigned_leading_audio'
 cue.write_text(original.replace('example.wav','../example.wav'));run([cue],2)
 run(['--make-example','fixture'],2)
 cue.write_text(original);wav.write_bytes(b'not a RIFF file');run([cue],2)
print(json.dumps({"installed_command":"cue-sample-plan","outside_checkout":True,"source_identity_matched":True,"contract_checks":"passed"}))
