"""Author-specified data serializer. Expected states below are explicit declarations,
not outputs of an evaluator or a reconstruction of any previous study."""
from pathlib import Path
import json,hashlib,subprocess,collections,shutil
P=Path('/home/toygar/Documents/ChatGPT/STRATEJIK_PLAN/evidence/standards_third_wave_2026-11-02/k1-author')
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
def envelope(rid,payload):
 s=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False)
 return {'record_id':rid,'payload_utf8':s,'payload_sha256':sha(s.encode())}
def unpack(r):return json.loads(r['payload_utf8'])
DISP=['SUBSTITUTION','CONFLICT','INVALID','EXPLICIT_FAILURE','INDETERMINATE','UNCONFIRMED','CONFIRMED']
RCLASS=['substitution','conflict','invalid','duplicate','matched','orphan']
notes=[]
for split in ['development','holdout']:
 for cat in range(1,13):
  h=split=='holdout';cid=('holdout' if h else 'dev')+f'-{cat:02}'
  # Distinct identifiers, targets and small stated native variations; never any evaluator result.
  target='ep-b' if h else 'ep-a'; other='ep-a' if h else 'ep-b'
  iid='instruction-beta' if h else 'instruction-alpha'; identity='scope-'+cid
  text=json.dumps({'control':'freeze' if not h else 'revoke','task':'task-'+cid},sort_keys=True,separators=(',',':'))
  digest=sha(text.encode());targets=[target,other] if cat==6 else [target]
  rule={'rule_id':'issuer-inclusion-v1','version':'1','frozen_time':0,'permitted_inputs':['instruction_id'],'evidence_available':True}
  exclusion={'rule_id':'target-exclusion-v1','version':'1','frozen_time':0,'permitted_inputs':['issuer_metadata','target_resolution'],'evidence_available':True}
  pop={'manifest_id':'manifest-'+cid,'manifest_instruction_ids':[iid],'included_instruction_ids':[iid],'inclusion_rule':rule,'exclusion_rule':exclusion,'cutoff':{'clock_id':'mono','time':10}}
  inst={'instruction_id':iid,'identity_scope':identity,'content_utf8':text,'content_sha256':digest,'resolution':{'status':'CLOSED','candidates':targets,'excluded':[],'coverage':{'status':'VERIFIED','evidence_refs':['profile:synthetic-deployment-inventory']}}}
  e={'schema':'acder02-control-benchmark-evidence-v1','case_id':cid,'profile_id':'acder02-control-benchmark-v1','population':pop,'instructions':[inst],'records':[],'queries':[]}
  o={'schema':'acder02-control-benchmark-oracle-v1','case_id':cid,'derivation':'Independent author judgments from -02 clauses, frozen profile and visible evidence; not evaluator output.','claims':[]}
  truth={'schema':'acder02-synthetic-latent-truth-v1','case_id':cid,'status':'Authored synthetic scenario specification, not measured runtime ground truth.','claim_truth':{},'latent_facts':[]}
  def rec(rid,kind,**kw):
   d={'kind':kind,'instruction_id':iid,'identity_scope':identity,'content_sha256':digest,'observer_id':target,'clock_id':'mono','time':3,'attempt_id':'attempt-1','target_id':target,'boundary_id':'target-entry'}
   d.update(kw);r=envelope(rid,d);e['records'].append(r);return r
  def issuer():
   r=rec('r-issuer','issuer_emission',observer_id='issuer',boundary_id='issuer-egress',time=1,target_ids=targets,resolution_ref=iid+'#resolution',outcome='EMITTED')
   d=unpack(r);d.pop('target_id');e['records'][-1]=envelope('r-issuer',d)
  def receiver(**kw):return rec('r-receiver','receiver_observation',outcome='RECEIVED',**kw)
  def ack(**kw):return rec('r-ack','transport_ack',observer_id='transport',boundary_id='transport-queue',time=2,outcome='QUEUED' if h else 'ACCEPTED',**kw)
  def enforce(outcome='APPLIED'):return rec('r-enforcement','enforcement',time=5,outcome=outcome,effective_time=5)
  def claim(qid,kind,state,latent,clauses,why,refs,conditions=(),qualification=None,scope=None,subject=None,missing=(),nonclaims=()):
   subj={'instruction_id':iid} if subject is None else subject
   sc={'clock_id':'mono','cutoff':10,'target_id':target}
   if scope:sc.update(scope)
   e['queries'].append({'claim_id':qid,'kind':kind,'subject':subj,'scope':sc})
   qual=qualification or ('FULLY_SUPPORTED' if state=='SUPPORTED' else 'NOT_SUPPORTED')
   o['claims'].append({'claim_id':qid,'kind':kind,'justified_state':state,'qualification':qual,'conditions':sorted(conditions),'draft_clauses':clauses,'evidence_basis':refs,'missing_evidence':list(missing),'rationale':why,'known_nonclaims':list(nonclaims),'ambiguous':False,'ambiguity_reason':None,'latent_truth_ref':'latent_truth.json#/claim_truth/'+qid})
   truth['claim_truth'][qid]=latent
  def integrity():
   claim('q-integrity','envelope_integrity','SUPPORTED',True,['5.2','5.13'],'Each referenced envelope contains the exact payload UTF-8 bytes whose SHA256 is stated. This is a byte-integrity statement, not validation of the event assertion.', ['record:'+r['record_id'] for r in e['records']],subject={'record_ids':[r['record_id'] for r in e['records']]},nonclaims=['event truth','authority','execution','effect'])
  def dispatch(state='SUPPORTED',latent=True):
   claim('q-issuer','issuer_dispatched',state,latent,['4.1','5.4'],'A bound issuer-egress observation is present.' if state=='SUPPORTED' else 'The population independently establishes the instruction, but no issuer-egress observation was supplied. A receiver observation cannot create it.',['record:r-issuer'] if state=='SUPPORTED' else ['input:population/manifest_instruction_ids'],() if state=='SUPPORTED' else ['missing_issuer_observation'],missing=[] if state=='SUPPORTED' else ['issuer-egress observation'],nonclaims=['receipt','enforcement','effect'])
  def receipt(state,latent,why,conditions=(),refs=None):
   claim('q-receipt','receiver_receipt',state,latent,['4.3','5.4','5.5','6.1'],why,refs or ['record:r-receiver'],conditions,scope={'boundary_id':'target-entry'},missing=['valid target-bound matching observation'] if state!='SUPPORTED' else [],nonclaims=['issuer dispatch','enforcement','execution','effect'])
  def all_delivery(state,latent,why,conditions=()):
   claim('q-all','all_required_delivery',state,latent,['4.2','5.10','5.11','6.2','6.5'],why,['input:population','input:instructions']+['record:'+r['record_id'] for r in e['records'] if unpack(r)['kind'] in ['issuer_emission','receiver_observation']],conditions,subject={'instruction_ids':pop['manifest_instruction_ids']},scope={'target_ids':targets,'population_scope':'manifest'},missing=[] if state=='SUPPORTED' else ['all required obligations established as CONFIRMED'],nonclaims=['deployment complete mediation','enforcement','effect'])
  def enforcement(state,latent,why,conditions=()):
   claim('q-enforcement','enforcement_applied',state,latent,['4.4','5.6'],why,['record:r-enforcement'] if any(r['record_id']=='r-enforcement' for r in e['records']) else ['input:records'],conditions,scope={'boundary_id':'target-entry','effective_time':5},missing=['attributable APPLIED assertion'] if state!='SUPPORTED' else [],nonclaims=['independent effect','execution completion','other targets'])
  def effect(state,latent,why,conditions=(),qid='q-effect',operation='operation-main',window=None,refs=None):
   claim(qid,'effect_observed',state,latent,['4.5','5.7','9.4'],why,refs or ['input:records'],conditions,scope={'operation_id':operation,'predicate_id':'no_provider_entry','window':window or [6,9],'boundary_id':'runtime-state'},missing=['matching predicate/operation/window observation'] if state!='SUPPORTED' else [],nonclaims=['unobserved operations','all deployment paths','reversal of prior effect'])
  def reconciliation(disps,structural,rc,why,unclosed=0,total=1,aggconditions=()):
   obs=[{'instruction_id':ii,'target_id':t,'disposition':d} for ii,t,d in disps]
   counts={k:0 for k in DISP}
   for _,_,d in disps:counts[d]+=1
   counts['total']=len(disps)
   rcounts={k:rc.get(k,0) for k in RCLASS};rcounts['total']=sum(rcounts.values())
   o['reconciliation']={'obligations':sorted(obs,key=lambda x:(x['instruction_id'],x['target_id'])),'instruction_accounting':{'total':total,'with_obligations':total-unclosed,'terminal_empty':0,'all_excluded':0,'target_resolution_unclosed':unclosed},'obligation_counts':counts,'receiver_record_counts':rcounts,'structural_result':structural,'aggregate_claim':{'qualification':'FULLY_SUPPORTED' if not aggconditions else 'CONDITIONALLY_SUPPORTED','conditions':list(aggconditions)},'draft_clauses':['5.4','5.10','5.11','6.1','6.2','6.4','6.5','6.6'],'rationale':why}
  if cat==1:
   issuer();ack();integrity();dispatch()
   receipt('INDETERMINATE',h,'The visible acknowledgement concerns the transport queue. No endpoint read/match observation supports target receipt.',['missing_receiver_observation'],['record:r-ack'])
   enforcement('INDETERMINATE',False,'Queue acknowledgement supplies no APPLIED observation.',['missing_enforcement_observation'])
   effect('INDETERMINATE',False,'No observation of the requested runtime predicate/window exists.',['missing_effect_observation'])
   reconciliation([(iid,target,'UNCONFIRMED')],'INCONCLUSIVE',{},'Issuer plus transport ACK does not supply endpoint receipt. No positive failure event is supplied.')
   truth['latent_facts']=[{'fact':'issuer crossed boundary','value':True},{'fact':'target read exact control','value':h},{'fact':'control applied','value':False},{'fact':'requested effect occurred','value':False}]
  elif cat==2:
   receiver()
   if h:enforce()
   integrity();dispatch('INDETERMINATE',True)
   receipt('SUPPORTED',True,'The valid receiver observation matches expected instruction metadata, exact digest, target and boundary. This receiver fact remains independently reportable despite missing issuer evidence.')
   all_delivery('INDETERMINATE',True,'Missing mandatory issuer observation prevents full structural delivery support, while receiver receipt remains supported.',['missing_issuer_observation'])
   if h:enforcement('SUPPORTED',True,'A valid separate attributable APPLIED observation exists; it does not repair absent issuer evidence.')
   reconciliation([(iid,target,'INDETERMINATE')],'INCONCLUSIVE',{'matched':1},'Missing issuer observation leaves the obligation INDETERMINATE; valid receiver remains matched and independently reportable.')
   truth['latent_facts']=[{'fact':'issuer actually dispatched but observation was not retained','value':True},{'fact':'target read control','value':True}]
  elif cat==3:
   inst['resolution']['status']='UNCLOSED';inst['resolution']['candidates']=[];inst['resolution']['coverage']={'status':'INDETERMINATE','evidence_refs':[]}
   issuer();receiver();integrity();dispatch()
   receipt('SUPPORTED',True,'An independently bound receiver fact is visible, although the required target population cannot be closed.')
   all_delivery('INDETERMINATE',False,'One observed receiver cannot establish a still-unclosed target population. No synthetic obligation is created.',['unclosed_target_resolution'])
   claim('q-mediation','complete_mediation','INDETERMINATE',False,['4.2','5.11','5.15','6.6'],'Required target resolution and deployment coverage remain unestablished.',['input:instructions/0/resolution'],['coverage_indeterminate','unclosed_target_resolution'],missing=['closed required target set','accepted coverage basis'],nonclaims=['all relevant paths covered'])
   reconciliation([],'INCONCLUSIVE',{'orphan':1},'The instruction is conserved in target_resolution_unclosed and creates no synthetic obligation; the receiver is not correlated to any expected obligation.',unclosed=1)
   truth['latent_facts']=[{'fact':'an additional required path exists outside the observed target','value':True},{'fact':'observed target received control','value':True}]
  elif cat==4:
   issuer();r=receiver();d=unpack(r);d.pop('attempt_id' if h else 'boundary_id');e['records'][-1]=envelope('r-receiver',d)
   integrity();dispatch();receipt('INDETERMINATE',h,'The receiver record is correlated by its available identity fields but lacks a mandatory native binding. Intact outer bytes do not validate endpoint receipt.',['invalid_receiver_record'])
   all_delivery('INDETERMINATE',h,'A correlated structurally invalid receiver record cannot confirm the obligation.',['invalid_receiver_record'])
   reconciliation([(iid,target,'INVALID')],'FAIL',{'invalid':1},'A positive mandatory native structural binding violation triggers the frozen INVALID-to-FAIL condition; this does not prove physical non-delivery.')
   truth['latent_facts']=[{'fact':'target actually received exact instruction','value':h},{'fact':'retained record lacks a required structural binding','value':True}]
  elif cat==5:
   issuer()
   if h:receiver(target_id=other,observer_id=other)
   else:receiver(content_sha256=sha(b'different governed control bytes'))
   integrity();dispatch()
   cs=['missing_receiver_observation'] if h else ['governed_content_substitution']
   receipt('INDETERMINATE',False,'A valid observation for another target cannot confirm this required target.' if h else 'Applicable same-identity issuer and receiver records disagree on governed content; a correlation is not confirmation.',cs)
   all_delivery('INDETERMINATE',False,'The exact required target/content obligation lacks confirmed matching receipt.',cs)
   reconciliation([(iid,target,'UNCONFIRMED' if h else 'SUBSTITUTION')],'INCONCLUSIVE' if h else 'FAIL',{'orphan':1} if h else {'substitution':1},'Unexpected-target record is ORPHAN and does not satisfy the required target.' if h else 'Positive same-identity content mismatch is SUBSTITUTION and frozen structural FAIL.')
   truth['latent_facts']=[{'fact':'required target received requested exact content','value':False},{'fact':'different target received control' if h else 'required target read substituted content','value':True}]
  elif cat==6:
   inst['resolution']['excluded']=[{'target_id':other,'reason':'no successful receiver observation','rule_id':'target-exclusion-v1','rule_version':'1','input_basis':'receiver_outcome','applied_time':8}]
   issuer();receiver();integrity();receipt('SUPPORTED',True,'The observed target has a matching valid receipt; this fact cannot satisfy the other required target.')
   all_delivery('INDETERMINATE',False,'A receiver-outcome-dependent exclusion is prohibited and cannot remove the unconfirmed target from the frozen population.',['outcome_adaptive_exclusion','unconfirmed_required_target'])
   claim('q-population','population_complete','SUPPORTED',True,['5.10','5.11'],'The bounded issuer instruction population is fully accounted; target exclusion manipulation is separately reported, not hidden as missing issuer population.',['input:population','input:instructions'],nonclaims=['valid target exclusion','all-target delivery','deployment mediation'])
   reconciliation([(iid,target,'CONFIRMED'),(iid,other,'UNCONFIRMED')],'FAIL',{'matched':1},'Outcome-adaptive exclusion is a positive frozen failure condition. Both original candidates remain required obligations; only one has receipt.')
   truth['latent_facts']=[{'fact':'observed target received','value':True},{'fact':'other required target received','value':False},{'fact':'all issuer instructions retained','value':True}]
  elif cat==7:
   issuer();receiver();integrity();receipt('SUPPORTED',True,'The exact target-bound receipt is valid under the accepted synthetic profile; its synthetic signature is also valid but adds no enforcement predicate.')
   all_delivery('SUPPORTED',True,'The sole required obligation has issuer and receiver observations with all exact structural bindings.')
   enforcement('INDETERMINATE',not h,'No enforcement observation was exposed; neither receipt nor a valid signature establishes APPLIED.',['missing_enforcement_observation'])
   effect('INDETERMINATE',False,'No matching runtime-state predicate observation was exposed.',['missing_effect_observation'])
   reconciliation([(iid,target,'CONFIRMED')],'PASS',{'matched':1},'Named population is closed and conserved and its sole obligation is confirmed; structural PASS does not establish enforcement/effect.')
   truth['latent_facts']=[{'fact':'receipt was signed with synthetic local Ed25519 key','value':True},{'fact':'control applied but no enforcement evidence exposed','value':not h},{'fact':'requested effect occurred','value':False}]
  elif cat==8:
   if not h:inst['resolution']['coverage']={'status':'DECLARED_ONLY','evidence_refs':[]}
   issuer();receiver();enforce();integrity();receipt('SUPPORTED',True,'A valid bound receipt is present.')
   enforcement('SUPPORTED',True,'The target reports APPLIED at its stated local effective boundary. This is not an independent effect observation.')
   effect('INDETERMINATE',not h,'An attributable APPLIED assertion supplies no observation of the requested runtime-state predicate/window.',['missing_effect_observation'])
   claim('q-mediation','complete_mediation','SUPPORTED' if h else 'INDETERMINATE',True,['4.2','5.15','6.6'],'Accepted synthetic coverage evidence and confirmed named obligations support this bounded deployment-path claim.' if h else 'Named-target delivery is confirmed, but deployment coverage is only declared. The permitted conditional qualification names the missing coverage predicate.',['input:instructions/0/resolution/coverage','record:r-issuer','record:r-receiver'],[] if h else ['coverage_declared_only'],qualification='FULLY_SUPPORTED' if h else 'CONDITIONALLY_SUPPORTED',subject={'instruction_ids':[iid]},scope={'target_ids':targets,'deployment_scope':'synthetic-node'},missing=[] if h else ['accepted coverage evidence'],nonclaims=['effect','external deployment coverage'])
   reconciliation([(iid,target,'CONFIRMED')],'PASS',{'matched':1},'Delivery is confirmed and structural accounting passes; effect remains a separate missing evidence dimension.')
   truth['latent_facts']=[{'fact':'target applied declared control semantics','value':True},{'fact':'requested effect actually occurred without exposed observation','value':not h}]
  elif cat==9:
   issuer();receiver();enforce()
   rec('r-entry','boundary_crossing',boundary_id='provider-entry',time=7 if h else 3,operation_id='operation-earlier',outcome='ENTERED')
   rec('r-effect-later','effect',observer_id='witness',boundary_id='runtime-state',time=9,operation_id='operation-later',predicate_id='no_provider_entry',window=[6,9],method='synthetic complete boundary-event observation',result='EFFECT_OBSERVED')
   integrity()
   claim('q-execution','execution_observed','SUPPORTED',True,['5.9','9.4'],'The bound observation establishes only that operation-earlier crossed provider-entry. Completion and consequential effects are not implied.',['record:r-entry'],scope={'operation_id':'operation-earlier','boundary_id':'provider-entry'},nonclaims=['completion','external effect','reversal'])
   claim('q-order','ordering','REFUTED' if h else 'SUPPORTED',not h,['5.9','9.4'],'The same accepted clock positively shows entry after activation, contradicting the requested before relationship.' if h else 'The entry and activation use the same stipulated monotonic clock; entry precedes activation.',['record:r-entry','record:r-enforcement'],[],scope={'before_record_id':'r-entry','after_record_id':'r-enforcement'},nonclaims=['completion','absence of earlier effect'])
   effect('SUPPORTED',True,'The witness observation matches exactly the later operation, predicate and window.',qid='q-effect-later',operation='operation-later',refs=['record:r-effect-later'])
   effect('REFUTED',False,'A native provider-entry observation for this exact operation occurs inside the requested same-clock no-entry window and positively contradicts that predicate. The different operation effect observation cannot override it.',['effect_scope_mismatch'],qid='q-effect-earlier',operation='operation-earlier',window=[6,9] if h else [2,4],refs=['record:r-effect-later','record:r-entry'])
   reconciliation([(iid,target,'CONFIRMED')],'PASS',{'matched':1},'Delivery remains confirmed; ordering and operation-specific effects do not inherit that result.')
   truth['latent_facts']=[{'fact':'operation admitted before activation in synthetic history','value':True},{'fact':'operation entered provider before activation','value':not h},{'fact':'later operation did not enter during its observed window','value':True},{'fact':'earlier operation was prevented from provider entry in requested window','value':False}]
  elif cat==10:
   issuer();rec('r-deadline','deadline',observer_id='reconciler',boundary_id='reconciliation-cutoff',time=10,deadline_time=10,observed_condition='NO_MATCHING_RECEIPT_AT_CUTOFF')
   integrity();dispatch();receipt('INDETERMINATE',not h,'The deadline record positively observes missing acknowledgement at cutoff; it does not prove target non-receipt.',['missing_receiver_observation'],['record:r-deadline'])
   all_delivery('INDETERMINATE',not h,'Deadline elapsed without a matching receipt leaves UNCONFIRMED; no scoped positive delivery-failure observation exists.',['unconfirmed_required_target'])
   reconciliation([(iid,target,'UNCONFIRMED')],'INCONCLUSIVE',{},'Deadline observation adds a diagnostic without turning absence into EXPLICIT_FAILURE or FAIL.')
   truth['latent_facts']=[{'fact':'target received despite missing acknowledgement' if not h else 'target did not receive, but evaluator has no proof of that fact','value':True}]
  elif cat==11:
   missing_id='instruction-omitted';pop['manifest_instruction_ids'].append(missing_id)
   issuer();receiver();integrity();receipt('SUPPORTED',True,'The included instruction has a valid receiver fact. The omitted instruction does not erase that narrower fact.')
   claim('q-population','population_complete','REFUTED',False,['5.10','5.11','6.4'],'The independent manifest positively names a second instruction that is absent from included IDs and instruction metadata. This is observed bounded-population omission, not a conjectured unknown external path.',['input:population/manifest_instruction_ids','input:population/included_instruction_ids','input:instructions'],['population_members_missing'],nonclaims=['complete bounded issuer population'])
   all_delivery('INDETERMINATE',False,'The omitted manifest member has no available target metadata and remains target_resolution_unclosed; no synthetic obligation may be invented.',['missing_instruction_metadata','population_members_missing'])
   reconciliation([(iid,target,'CONFIRMED')],'FAIL',{'matched':1},'Known omission triggers the frozen positive failure condition; both instructions are counted, and the missing metadata instruction is unclosed.',unclosed=1,total=2)
   truth['latent_facts']=[{'fact':'omitted instruction exists in frozen issuer population','value':True},{'fact':'omitted instruction was delivered to all its real required targets','value':False}]
  elif cat==12:
   issuer();receiver();enforce('UNKNOWN' if not h else 'REFUSED')
   mapping={'APPLIED':'APPLIED','REFUSED':'APPLIED' if h else 'REFUSED','NO_EFFECT':'NO_EFFECT','UNKNOWN':'UNKNOWN' if h else 'APPLIED'}
   rec('r-transform','transformation',observer_id='gateway',boundary_id='gateway-egress',time=6,source_record_id='r-enforcement',source_state='REFUSED' if h else 'UNKNOWN',destination_state='APPLIED',state_mapping=mapping)
   rec('r-ack','transport_ack',observer_id='gateway',boundary_id='transport-queue',time=7,outcome='ACCEPTED',transformation_record_id='r-transform')
   integrity();receipt('SUPPORTED',True,'The original source-bound receipt remains available and valid; downstream semantic alteration does not erase this source fact.')
   enforcement('REFUTED' if h else 'INDETERMINATE',False,'The native source expressly REFUSED application; a gateway APPLIED representation contradicts the source.' if h else 'The source outcome is UNKNOWN. A gateway rewriting UNKNOWN to APPLIED supplies no attributable APPLIED evidence.',['semantic_mapping_not_lossless'] if h else ['semantic_mapping_not_lossless','source_state_does_not_establish_applied'])
   claim('q-semantics','semantic_preservation','REFUTED',False,['5.13','5.16'],'The explicit transformation collapses a distinct native state into APPLIED, although every outer envelope digest remains intact. This positively contradicts lossless preservation.',['record:r-enforcement','record:r-transform'],['semantic_mapping_not_lossless'],scope={'transformation_record_id':'r-transform'},nonclaims=['lossless downstream semantics','enforcement from gateway ACK'])
   reconciliation([(iid,target,'CONFIRMED')],'PASS',{'matched':1},'Delivery structure is intact. Semantic preservation and enforcement claims are separately qualified/refuted and cannot be derived from PASS.')
   truth['latent_facts']=[{'fact':'source target applied the control','value':False},{'fact':'gateway altered source meaning','value':True}]
  # Freeze author artifacts; no expectation is computed from a comparator.
  path=P/split/cid
  dump(path/'evidence.json',e);dump(path/'oracle.json',o);dump(path/'latent_truth.json',truth)
  notes.append({'case_id':cid,'category_id':f'cat-{cat:02}','split':split,'claims':len(e['queries'])})

# Genuine synthetic-key signatures for both preselected category-7 receipts.
keys=P/'signature_fixture';keys.mkdir(exist_ok=True)
private=keys/'SYNTHETIC_TEST_ONLY_PRIVATE_KEY.pem';public=keys/'SYNTHETIC_TEST_ONLY_PUBLIC_KEY.pem'
subprocess.run(['openssl','genpkey','-algorithm','ED25519','-out',str(private)],check=True,capture_output=True)
subprocess.run(['openssl','pkey','-in',str(private),'-pubout','-out',str(public)],check=True,capture_output=True)
version=subprocess.check_output(['openssl','version'],text=True).strip()
for split,cid in [('development','dev-07'),('holdout','holdout-07')]:
 path=P/split/cid;e=json.loads((path/'evidence.json').read_text());r=next(r for r in e['records'] if r['record_id']=='r-receiver')
 payload=path/'signed_payload.bin';sig=path/'signature.bin';payload.write_bytes(r['payload_utf8'].encode())
 sign=['openssl','pkeyutl','-sign','-inkey',str(private),'-rawin','-in',str(payload),'-out',str(sig)]
 verify=['openssl','pkeyutl','-verify','-pubin','-inkey',str(public),'-rawin','-in',str(payload),'-sigfile',str(sig)]
 subprocess.run(sign,check=True,capture_output=True);v=subprocess.run(verify,check=True,capture_output=True,text=True)
 r['signature']={'algorithm':'Ed25519','public_key_pem':public.read_text(),'signature_hex':sig.read_bytes().hex()};dump(path/'evidence.json',e)
 dump(path/'signature_verification.json',{'schema':'synthetic-ed25519-author-verification-v1','openssl_version':version,'payload_sha256':sha(payload.read_bytes()),'signature_sha256':sha(sig.read_bytes()),'public_key_sha256':sha(public.read_bytes()),'verify_command':verify,'exit_code':v.returncode,'stdout':v.stdout.strip(),'synthetic_fixture_key_only':True,'evaluator_verification_claim':False,'nonclaims':['external identity','authority','event truth','enforcement','effect']})
dump(P/'CASE_COUNTS.json',{'schema':'acder02-case-counts-v1','case_count':24,'development_count':12,'holdout_count':12,'cases':notes})
(P/'AUTHORING_NOTES.md').write_text('''# Authoring record

The case/oracle package was authored without executing a comparator. Explicit justified states, latent boolean/null values, expected structural dispositions and rationales were written as separate declarations in a serialization recipe; the recipe performs no evaluation of observations into states. It computes only byte digests, JSON serialization and bookkeeping counts from the manually declared expected disposition list. The same author knows both development and holdout data; the holdout is withheld only from the evaluator author until logic freeze. This is no external independence claim.

The serializer is retained under holdout/authoring_recipe.py because it includes withheld scenario/oracle content. Do not read it before the logic-freeze gate. All final JSON bytes, not regeneration with a fresh random signing key, are the reproducible frozen dataset. The labeled synthetic private key is intentionally a public test fixture with no external authority; both actual signatures were verified locally with OpenSSL and the verification records are pinned.
''')
shutil.copyfile(__file__,P/'holdout/authoring_recipe.py')
print('Authored 24 evidence/oracle/latent case triplets; no comparator executed.')
