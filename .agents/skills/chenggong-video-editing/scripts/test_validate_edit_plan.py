"""Engineering invariants with temporary fixtures; media playback is checked separately."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from validate_edit_plan import validate, validate_workflow, request_fingerprint


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        assert self.base.resolve().parent == Path.cwd().resolve()
        (self.base/'rough.mp4').write_bytes(b'source media fixture')
        (self.base/'rough.srt').write_text('1\n00:00:00,000 --> 00:00:10,000\n现在展示素材\n',encoding='utf-8')
        (self.base/'approved.mp4').write_bytes(b'approved output fixture')
        self.plan = {'video':'rough.mp4','srt':'rough.srt','duration':10,
            'locked':[{'path':'approved.mp4','sha256':hashlib.sha256((self.base/'approved.mp4').read_bytes()).hexdigest()}],
            'scenes':[{'id':'S1','start':0,'end':10,'text':'现在展示素材','layers':[
                {'id':'media','trigger':'展示素材','cue_time':2,'in':2,'out':6,'asset':'rough.mp4',
                 'source_in':0,'source_out':8,'source_duration':10,'speed':2}]}]}

    def test_style_is_not_an_engineering_requirement(self):
        self.assertEqual(validate(self.plan,self.base),[])
        for style in [{'font':'Microsoft YaHei','accent':'#593D91'},
                      {'font':'Arial','accent':'#c7ff4d','layout':'original-scene'}]:
            with self.subTest(style=style):
                p=copy.deepcopy(self.plan);p['style']=style
                self.assertEqual(validate(p,self.base),[])

    def test_missing_files_timing_and_source_mismatches_are_rejected(self):
        mutations=[lambda p:p.update(video='missing.mp4'),
            lambda p:p.update(srt='missing.srt'),
            lambda p:p.update(duration=float('nan')),
            lambda p:p['scenes'][0].update(start=1),
            lambda p:p['scenes'][0].update(end=9),
            lambda p:p['scenes'][0]['layers'][0].update(asset='missing.png'),
            lambda p:p['scenes'][0]['layers'][0].update(out=11),
            lambda p:p['scenes'][0]['layers'][0].update(speed=1),
            lambda p:p['scenes'][0]['layers'][0].update(source_out=12),
            lambda p:p['scenes'][0]['layers'][0].update(cue_time=4),
            lambda p:p['scenes'][0]['layers'][0].update(trigger='无关内容')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                p=copy.deepcopy(self.plan);mutation(p)
                self.assertTrue(validate(p,self.base))

    def test_frozen_outputs_detect_real_changes(self):
        self.assertEqual(validate(self.plan,self.base),[])
        (self.base/'approved.mp4').write_bytes(b'changed output')
        self.assertIn('locked file changed',validate(self.plan,self.base))

    def test_uncaptioned_work_does_not_require_srt(self):
        p=copy.deepcopy(self.plan)
        p['captions_enabled']=False
        p.pop('srt')
        self.assertEqual(validate(p,self.base),[])

    def test_calendar_must_cover_spoken_sentence(self):
        p=copy.deepcopy(self.plan)
        p['scenes'][0]['layers'][0]['speech_end']=6.2
        self.assertTrue(validate(p,self.base))
        p['scenes'][0]['layers'][0]['out']=6.2
        p['scenes'][0]['layers'][0]['source_out']=8.4
        self.assertEqual(validate(p,self.base),[])


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.source=dict(self.record('new-cut.mp4',b'current input'),duration=10,has_audio=True)
        self.frame=self.record('frame.png',b'current preview')
        self.output=self.record('result.mp4',b'rendered result')
        self.proof=self.record('review.md',b'reviewer coverage record')
        result={'status':'passed','method':'review','coverage':'full','detail':'checked the current deliverable','evidence':[self.proof]}
        self.state={
          'workflow_version':1,
          'source':self.source,
          'request':{'id':'req1','user_text':'Use the latest cut, with fixed bottom captions',
                     'message_index':1,
                     'source_sha256':self.source['sha256'],'visual_scopes':['captions'],
                     'visual_ranges':{'captions':[[0,10]]},
                     'requirements':[{'id':'position','user_text':'fixed bottom','acceptance':'captions stay lower centre'}]},
          'reviews':[{'scope':'captions','source_sha256':self.source['sha256'],'frames':[dict(self.frame,at=5)],'ranges':[[0,10]],
                      'status':'approved','basis':{'kind':'keyframe_review','user_text':'Yes, use this preview.',
                      'preview_message_index':2,'confirmation_message_index':3}}],
          'output':self.output,
          'verification':{'source_sha256':self.source['sha256'],'output_sha256':self.output['sha256'],'request_id':'req1',
                          'requirements':[dict(result,id='position')],
                          'technical':copy.deepcopy(result),'visual':dict(result,method='continuous_visual_review'),
                          'audio':dict(result,method='continuous_audio_review'),'playback':dict(result,method='user_entry_playback')}}
        self.confirm(self.state)
        self.bind_report(self.state)

    def confirm(self,state):
        digest=request_fingerprint(state['request'])
        for review in state['reviews']:review['request_sha256']=digest
        state['verification']['request_sha256']=digest

    def bind_report(self,state):
        v=state['verification']
        checks={x['id']:x for x in v['requirements']}
        checks.update({k:v[k] for k in ('technical','visual','audio','playback')})
        payload={k:v[k] for k in ('source_sha256','output_sha256','request_sha256')}
        payload['checks']={k:{f:r.get(f) for f in ('status','method','coverage')} for k,r in checks.items()}
        report=dict(self.record('bound.json',json.dumps(payload).encode()),kind='verification_report')
        for check in checks.values():
            check['evidence']=[self.proof,report]

    def record(self,name,content):
        (self.base/name).write_bytes(content)
        return {'path':name,'sha256':hashlib.sha256(content).hexdigest()}

    def run_gate(self,s,stage='render',expected_source=None):
        return validate_workflow(s,self.base,stage,expected_source)

    def test_first_draft_without_frames_or_approval_stops(self):
        s=copy.deepcopy(self.state);s['reviews']=[]
        self.assertTrue(self.run_gate(s))
        self.assertEqual(self.run_gate(s,'keyframes'),[])

    def test_approval_of_opening_does_not_cover_new_body(self):
        s=copy.deepcopy(self.state)
        s['request']['visual_scopes'].append('body')
        s['request']['visual_ranges']['body']=[[0,10]]
        self.assertTrue(self.run_gate(s))
        review=copy.deepcopy(s['reviews'][0]);review['scope']='body'
        s['reviews'].append(review)
        self.confirm(s)
        self.assertEqual(self.run_gate(s),[])

    def test_new_user_input_cannot_reuse_old_frames(self):
        fresh=self.record('newer.mp4',b'new duration and footage')
        self.assertTrue(self.run_gate(self.state,expected_source='newer.mp4'))
        s=copy.deepcopy(self.state);s['source']=fresh;s['request']['source_sha256']=fresh['sha256']
        self.assertTrue(self.run_gate(s))

    def test_partial_confirmation_checks_only_the_requested_render_scope(self):
        s=copy.deepcopy(self.state)
        s['request']['visual_scopes'].append('body')
        s['request']['visual_ranges']['body']=[[5,10]]
        self.confirm(s)
        self.assertTrue(self.run_gate(s))
        self.assertEqual(validate_workflow(s,self.base,'render',selected_scopes=['captions']),[])
        self.assertTrue(validate_workflow(s,self.base,'render',selected_scopes=['body']))
        self.assertTrue(validate_workflow(s,self.base,'render',selected_scopes=['unknown']))
        self.assertTrue(validate_workflow(s,self.base,'deliver',selected_scopes=['captions']))

    def test_supporting_recording_changed_at_the_same_path_blocks_render(self):
        s=copy.deepcopy(self.state)
        s['request']['supporting_sources']=[self.record('screen.mp4',b'screen recording')]
        self.confirm(s)
        self.assertEqual(self.run_gate(s),[])
        (self.base/'screen.mp4').write_bytes(b'replacement screen recording')
        self.assertIn('supporting source 1: file changed since recorded', self.run_gate(s))
        (self.base/'screen.mp4').unlink()
        self.assertIn('supporting source 1: file missing',self.run_gate(s,'keyframes'))

    def test_modifying_an_approved_frame_invalidates_it(self):
        (self.base/'frame.png').write_bytes(b'different framing')
        self.assertTrue(self.run_gate(self.state))

    def test_reexport_invalidates_old_checks(self):
        s=copy.deepcopy(self.state)
        s['output']=self.record('reexport.mp4',b'reexport with different captions')
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_technical_success_alone_is_incomplete(self):
        s=copy.deepcopy(self.state)
        s['verification']['audio']['status']='partial'
        s['verification']['audio']['method']='ASR'
        s['verification']['playback']['status']='not_run'
        self.assertTrue(self.run_gate(s,'deliver'))
        self.assertEqual(self.run_gate(s),[])

    def test_viewer_window_title_alone_is_not_playback(self):
        s=copy.deepcopy(self.state)
        s['verification']['playback']['method']='window_title'
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_full_scope_current_evidence_can_pass(self):
        self.assertEqual(self.run_gate(self.state,'deliver'),[])

    def test_missing_or_changed_evidence_fails_delivery(self):
        (self.base/'review.md').write_bytes(b'stale or unrelated')
        self.assertTrue(self.run_gate(self.state,'deliver'))

    def test_fixed_bottom_requirement_cannot_disappear(self):
        s=copy.deepcopy(self.state)
        s['verification']['requirements']=[]
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_asr_cannot_claim_complete_listening(self):
        s=copy.deepcopy(self.state)
        s['verification']['audio']['method']='ASR'
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_frame_sampling_cannot_claim_complete_viewing(self):
        s=copy.deepcopy(self.state)
        s['verification']['visual']['method']='frame_sampling'
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_playback_cannot_be_declared_inapplicable(self):
        s=copy.deepcopy(self.state)
        s['verification']['playback']={'status':'not_applicable','detail':'file exists'}
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_only_truly_silent_source_can_skip_audio(self):
        s=copy.deepcopy(self.state)
        s['verification']['audio']={'status':'not_applicable','detail':'silent source',
                                    'method':'metadata_probe','coverage':'full'}
        self.bind_report(s)
        self.assertTrue(self.run_gate(s,'deliver'))
        s['source']['has_audio']=False
        self.assertEqual(self.run_gate(s,'deliver'),[])

    def test_exact_authorized_correction_does_not_require_new_permission(self):
        s=copy.deepcopy(self.state)
        s['request']['approval_mode']='directed_change'
        s['reviews'][0]['basis']={'kind':'directed_change','user_text':'with fixed bottom captions'}
        self.confirm(s)
        self.assertEqual(self.run_gate(s),[])

    def test_old_approval_cannot_be_relabelled_as_current_direct_instruction(self):
        s=copy.deepcopy(self.state)
        s['request']['user_text']='根据我的口播内容把素材加到对应的地方，缺实操时加一点包装。'
        s['reviews'][0]['basis']={'kind':'directed_change','user_text':'可以，就按这版合成整条视频吧。'}
        self.confirm(s)
        self.assertIn('captions: approval does not match the current request mode',self.run_gate(s))
        s['request']['approval_mode']='directed_change'
        self.confirm(s)
        self.assertIn('captions: direct instruction must be quoted from the current request',self.run_gate(s))

    def test_preview_must_precede_confirmation_in_current_chat(self):
        basis=self.state['reviews'][0]['basis']
        for preview,confirmation in [(None,3),(2,None),(1,3),(2,2),(3,2)]:
            with self.subTest(preview=preview,confirmation=confirmation):
                basis.update(preview_message_index=preview,confirmation_message_index=confirmation)
                self.assertIn('captions: need a delivered preview and a later user confirmation in this chat',
                              self.run_gate(self.state))

    def test_explicit_skip_from_current_request_allows_no_frames(self):
        self.state['request'].update(approval_mode='explicit_skip',user_text='跳过关键帧，直接导出这段。')
        self.state['reviews'][0].update(frames=[],basis={'kind':'explicit_skip','user_text':'跳过关键帧，直接导出这段。'})
        self.confirm(self.state)
        self.assertEqual(self.run_gate(self.state),[])

    def test_same_scope_new_request_invalidates_old_approval(self):
        s=copy.deepcopy(self.state)
        s['request']['user_text']='Redesign the opening with a new background'
        self.assertTrue(self.run_gate(s))

    def test_preview_from_outside_approved_part_is_rejected(self):
        s=copy.deepcopy(self.state)
        s['request']['visual_ranges']['captions']=[[0,3]]
        s['reviews'][0]['ranges']=[[0,3]]
        self.confirm(s)
        self.assertTrue(self.run_gate(s))

    def test_preview_at_cut_boundary_is_outside_retained_interval(self):
        self.state['reviews'][0]['frames'][0]['at'] = 10
        self.assertIn('captions/frame-1: preview is outside its timeline range', self.run_gate(self.state))
        self.state['reviews'][0]['frames'][0]['at'] = 9.966667
        self.assertEqual(self.run_gate(self.state), [])

    def test_evidence_cannot_be_rebound_to_another_output_in_state(self):
        s=copy.deepcopy(self.state)
        s['output']=self.source
        s['verification']['output_sha256']=self.source['sha256']
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_requested_requirement_cannot_be_marked_inapplicable(self):
        s=copy.deepcopy(self.state)
        s['verification']['requirements'][0]['status']='not_applicable'
        self.bind_report(s)
        self.assertTrue(self.run_gate(s,'deliver'))

    def test_changed_subtitle_attachment_is_detected(self):
        s=copy.deepcopy(self.state)
        s['output']['attachments']=[self.record('captions.srt',b'original captions')]
        self.assertEqual(self.run_gate(s,'deliver'),[])
        (self.base/'captions.srt').write_bytes(b'different captions')
        self.assertTrue(self.run_gate(s,'deliver'))


if __name__ == '__main__':
    unittest.main()
