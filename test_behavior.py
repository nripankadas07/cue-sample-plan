import hashlib
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from cue_sample_plan import plan,parse_cue,wave_info,make_example,timestamp

class CueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)/'example';make_example(self.d);self.cue=self.d/'example.cue'
    def tearDown(self):self.tmp.cleanup()
    def rewrite(self,text):self.cue.write_text(text,encoding='utf-8');return self.cue
    def test_sample_exact_track_and_gap_partitions(self):
        r=plan(self.cue);spans=r['files'][0]['partitions'];self.assertEqual([(s['kind'],s['start_sample_frame'],s['end_sample_frame_exclusive']) for s in spans],[('track_audio',0,44100),('recorded_pregap',44100,88200),('track_audio',88200,176400)]);self.assertFalse(r['findings'])
    def test_full_byte_coverage_and_unchanged_source(self):
        p=self.d/'example.wav';before=hashlib.sha256(p.read_bytes()).hexdigest();r=plan(self.cue)['files'][0];self.assertEqual(sum(x['sample_frames'] for x in r['partitions']),176400);self.assertEqual(r['partitions'][0]['start_file_byte'],44);self.assertEqual(r['partitions'][-1]['end_file_byte_exclusive'],p.stat().st_size);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),before)
    def test_unassigned_leading_audio_reported(self):
        r=plan(self.rewrite('FILE "example.wav" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:01:00\n'));self.assertEqual(r['findings'][0]['sample_frames'],44100);self.assertEqual(r['files'][0]['partitions'][0]['kind'],'unassigned_leading_audio')
    def test_first_recorded_gap_not_discarded(self):
        r=plan(self.rewrite('FILE "example.wav" WAVE\nTRACK 01 AUDIO\nINDEX 00 00:00:00\nINDEX 01 00:01:00\n'));self.assertEqual(r['files'][0]['partitions'][0]['kind'],'recorded_pregap');self.assertFalse(r['findings'])
    def test_two_files_reset_local_time(self):
        (self.d/'two.wav').write_bytes((self.d/'example.wav').read_bytes());r=plan(self.rewrite('FILE "example.wav" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:00:00\nFILE "two.wav" WAVE\nTRACK 02 AUDIO\nINDEX 01 00:00:00\n'));self.assertEqual(len(r['files']),2)
    def test_nonrepresentable_index_refused(self):
        p=self.d/'example.wav'
        with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*32000)
        with self.assertRaisesRegex(ValueError,'exact sample-frame'):plan(self.rewrite('FILE "example.wav" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:00:01\n'))
    def test_timestamp_bounds(self):
        self.assertEqual(timestamp('01:02:03'),4653)
        for x in ['00:60:00','00:00:75','0:00:00','-1:00:00']:
            with self.assertRaises(ValueError):timestamp(x)
    def test_bad_track_index_order(self):
        base='FILE "example.wav" WAVE\nTRACK 01 AUDIO\n'
        for b in ['INDEX 01 00:01:00\nINDEX 00 00:00:00','INDEX 00 00:02:00\nINDEX 01 00:01:00','INDEX 01 00:01:00\nINDEX 01 00:02:00']:
            with self.subTest(b=b),self.assertRaises(ValueError):plan(self.rewrite(base+b))
    def test_overlap_and_zero_duration_track(self):
        for second in ['INDEX 01 00:00:00','INDEX 00 00:00:00\nINDEX 01 00:01:00']:
            text='FILE "example.wav" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:00:00\nTRACK 02 AUDIO\n'+second
            with self.assertRaises(ValueError):plan(self.rewrite(text))
    def test_index_at_or_beyond_eof(self):
        with self.assertRaises(ValueError):plan(self.rewrite('FILE "example.wav" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:04:00'))
    def test_basename_and_symlink_boundary(self):
        for name in ['../example.wav','/tmp/a.wav','C:a.wav','x\\a.wav']:
            with self.assertRaises(ValueError):parse_cue(f'FILE "{name}" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:00:00')
        (self.d/'link.wav').symlink_to(self.d/'example.wav')
        with self.assertRaises(ValueError):plan(self.rewrite('FILE "link.wav" WAVE\nTRACK 01 AUDIO\nINDEX 01 00:00:00'))
    def test_unsupported_gaps_and_indices(self):
        for command in ['PREGAP 00:01:00','POSTGAP 00:01:00','INDEX 02 00:03:00']:
            with self.assertRaises(ValueError):parse_cue(self.cue.read_text()+command)
    def test_track_sequence_and_complete_files(self):
        for text in ['FILE "example.wav" WAVE','FILE "example.wav" WAVE\nTRACK 02 AUDIO\nINDEX 01 00:00:00','FILE "example.wav" WAVE\nTRACK 01 AUDIO']:
            with self.assertRaises(ValueError):parse_cue(text)
    def test_duplicate_file_block(self):
        with self.assertRaises(ValueError):parse_cue(self.cue.read_text()+'FILE "example.wav" WAVE\n')
    def test_bad_riff_size_or_magic(self):
        p=self.d/'example.wav';raw=p.read_bytes()
        for bad in [b'RIFX'+raw[4:],raw[:-1],raw[:4]+b'\0\0\0\0'+raw[8:]]:
            p.write_bytes(bad)
            with self.assertRaises(ValueError):wave_info(p)
    def test_bad_block_alignment(self):
        p=self.d/'example.wav';raw=bytearray(p.read_bytes());struct.pack_into('<H',raw,32,3);p.write_bytes(raw)
        with self.assertRaises(ValueError):wave_info(p)
    def test_unknown_odd_chunk_and_padding(self):
        p=self.d/'example.wav';raw=p.read_bytes();chunk=b'JUNK'+struct.pack('<I',3)+b'abc\0';raw=raw[:12]+chunk+raw[12:];raw=raw[:4]+struct.pack('<I',len(raw)-8)+raw[8:];p.write_bytes(raw);r=wave_info(p);self.assertEqual(r['data_offset'],56);self.assertEqual(r['ignored_chunks'],{'JUNK':1})
    def test_duplicate_data_chunk(self):
        p=self.d/'example.wav';raw=p.read_bytes()+b'data\0\0\0\0';raw=raw[:4]+struct.pack('<I',len(raw)-8)+raw[8:];p.write_bytes(raw)
        with self.assertRaises(ValueError):wave_info(p)
    def test_metadata_ignored_and_existing_example_refused(self):
        r=plan(self.rewrite('REM synthetic\nTITLE "Not copied music"\n'+self.cue.read_text()));self.assertEqual(r['ignored_metadata'],{'REM':1,'TITLE':1})
        with self.assertRaises(FileExistsError):make_example(self.d)
    def test_stereo_sample_frames(self):
        p=self.d/'example.wav'
        with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000);w.writeframes(b'\0'*6*48000*4)
        r=plan(self.cue)['files'][0];self.assertEqual(r['wave']['sample_frames'],192000);self.assertEqual(r['partitions'][0]['sample_frames'],48000)

if __name__=='__main__':unittest.main()
