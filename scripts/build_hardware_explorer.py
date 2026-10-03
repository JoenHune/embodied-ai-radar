#!/usr/bin/env python3
"""Build a display-only hardware explorer from public records and existing catalog evidence."""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from export_token_free_public import sanitize, _write_json
ROOT=Path(__file__).resolve().parents[1]
GROUPS=[('compute','算力设备',['compute_platform']),('platform','机器人整机',['robot_platform']),('arms','机械臂与双臂系统',['robot_arm']),('hands','灵巧手',['dexterous_hand']),('tools','夹爪与末端工具',['gripper']),('sensors','传感器',['vision_sensor','tactile_sensor','force_sensor','inertial_sensor']),('capture','遥操作与采集设备',['data_collection'])]
CATEGORY_GROUP={c:g for g,_,cs in GROUPS for c in cs}
PRESENTATION_OVERRIDES={'model:aloha-system':'arms','model:aloha-2-system':'arms'}
SUBLABELS={'vision_sensor':'视觉与空间感知','tactile_sensor':'触觉','force_sensor':'力与力矩','inertial_sensor':'惯性'}
def rows(path):
    if path.is_dir():
        for p in sorted(path.glob('*.jsonl')):yield from rows(p)
    elif path.exists():
        with path.open() as stream:
            for line in stream:
                if line.strip():yield json.loads(line)
def month(w):
    s=w.get('first_public_date');precision=w.get('first_public_date_precision')
    if precision not in ('month','day') or not isinstance(s,str) or not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?',s):return None
    try:date.fromisoformat(s if len(s)==10 else s+'-01')
    except ValueError:return None
    return s[:7]
def citation_index(publications):
    result=defaultdict(list)
    for p in publications:
        n=p.get('citation_count_snapshot');sid=p.get('semantic_scholar_id');stamp=p.get('citation_snapshot_date')
        if type(n) is not int or n<0 or n>2**53-1 or not isinstance(sid,str) or not re.fullmatch(r'[0-9a-fA-F]{40}',sid) or not isinstance(stamp,str):continue
        try:date.fromisoformat(stamp)
        except ValueError:continue
        item={'count':n,'snapshot_date':stamp,'source_name':'Semantic Scholar','source_url':'https://www.semanticscholar.org/paper/'+sid,'snapshot_basis':'configured_collection_window_end','queried_at':None,'paper_id':sid}
        keys={p.get('work_id'),('doi:'+p['doi'].lower()) if p.get('doi') else None,('arxiv:'+p['arxiv_id']) if p.get('arxiv_id') else None}
        for k in keys:
            if k:result[k].append(item)
    return result
def select_citation(w,index):
    choices=[r for k in {w['work_id'],*w.get('aliases',[])} for r in index.get(k,[])]
    if not choices:return None
    # Never add version counts or arbitrarily choose between distinct S2 identities.
    if len({r['paper_id'] for r in choices})!=1:return None
    newest=max(r['snapshot_date'] for r in choices);latest=[r for r in choices if r['snapshot_date']==newest]
    if len({r['count'] for r in latest})!=1:return None
    return {k:v for k,v in latest[0].items() if k!='paper_id'}
def build(source,catalog,publications,dictionary,api):
    raw=source.read_bytes() if source.exists() else b'';records={}
    for line in raw.splitlines():
        r=sanitize(json.loads(line));wid=r['work_id']
        if wid in records:raise ValueError('duplicate_public_work')
        records[wid]=r
    pubs=json.loads(publications.read_text()) if publications.exists() else []
    ci=citation_index(pubs);metadata={};catalog_months=Counter();catalog_total=0;catalog_unknown=0;eligible=0
    for w in rows(catalog/'works'):
        catalog_total+=1;m=month(w)
        if isinstance(w.get('identifiers',{}).get('arxiv'),str):
            eligible+=1
            if m:catalog_months[m]+=1
            else:catalog_unknown+=1
        if w['work_id'] in records:metadata[w['work_id']]={'title':w.get('title_zh') or w.get('title') or w['work_id'],'date':w.get('first_public_date'),'date_precision':w.get('first_public_date_precision'),'month':m,'citation':select_citation(w,ci)}
    entries=json.loads(dictionary.read_text()).get('entries',[]) if dictionary.exists() else []
    devices={e['dictionary_id']:{'id':e['dictionary_id'],'name':e['name'],'category':e['category'],'group':PRESENTATION_OVERRIDES.get(e['dictionary_id'],CATEGORY_GROUP.get(e['category'],'other')),'subcategory':SUBLABELS.get(e['category']),'aliases':e.get('aliases',[]),'identity_level':e.get('identity_level','unspecified'),'work_count':0} for e in entries}
    output=[];device_works=defaultdict(set)
    for wid,r in sorted(records.items()):
        matches=[];by_device={}
        for m in r['matches']:
            did=m['dictionary_id']
            if did not in devices:devices[did]={'id':did,'name':m['name'],'category':m['category'],'group':CATEGORY_GROUP.get(m['category'],'other'),'subcategory':SUBLABELS.get(m['category']),'aliases':[],'identity_level':'unspecified','work_count':0}
            # Preserve distinct contexts/flags. Only exact repeated mentions collapse.
            key=(did,m['context_only'],m['simulation_word_present'],m['negation_word_present'])
            if key not in by_device:
                by_device[key]={'device_id':did,'group':devices[did]['group'],'context_only':m['context_only'],'simulation':m['simulation_word_present'],'negation':m['negation_word_present'],'usage_verified':False,'locators':[]}
            if m['source_locator'] and m['source_locator'] not in by_device[key]['locators']:by_device[key]['locators'].append(m['source_locator'])
            device_works[did].add(wid)
        matches=list(by_device.values())
        for m in matches:m['locators']=m['locators'][:3]
        output.append({'id':wid,**metadata.get(wid,{'title':wid,'date':None,'date_precision':None,'month':None,'citation':None}),'source_url':r['source_url'],'process_state':r['process_state'],'source_state':r['source_state'],'matches':matches})
    for did,d in devices.items():d['work_count']=len(device_works[did])
    manifest=json.loads((catalog/'manifest.json').read_text()) if (catalog/'manifest.json').exists() else {}
    value={'schema_version':'1','records_sha256':hashlib.sha256(raw).hexdigest(),'catalog_hash':manifest.get('catalog_hash'),'data_through':manifest.get('data_through'),'catalog_total':catalog_total,'arxiv_catalog_total':eligible,'catalog_months':dict(sorted(catalog_months.items())),'catalog_unknown_month':catalog_unknown,'categories':[{'id':g,'name':name,'categories':cs} for g,name,cs in GROUPS],'devices':list(devices.values()),'rows':output,'citation_coverage':{'available':sum(w['citation'] is not None for w in output),'total':len(output),'snapshot_dates':sorted({w['citation']['snapshot_date'] for w in output if w['citation']}),'actual_query_time_available':False},'unknown_month_count':sum(w['month'] is None for w in output),'usage_verified_count':0}
    _write_json(api/'explorer.json',value)
    return value
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'data/token-free-public/records.jsonl');p.add_argument('--catalog',type=Path,default=ROOT/'data/catalog');p.add_argument('--publications',type=Path,default=ROOT/'data/publications.json');p.add_argument('--dictionary',type=Path,default=ROOT/'config/hardware-dictionary.json');p.add_argument('--api',type=Path,default=ROOT/'docs/public/api/v1/token-free');a=p.parse_args();v=build(a.source,a.catalog,a.publications,a.dictionary,a.api);print(json.dumps({'rows':len(v['rows']),'citation_coverage':v['citation_coverage'],'unknown_months':v['unknown_month_count']}))
