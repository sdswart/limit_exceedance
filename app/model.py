#!/usr/bin/python
import os
import json
import logging
import numpy as np
from storage import S3Storage, LocalStorage
import requests

logger = logging.getLogger(__name__)

def get_storage(config,verify=True):
    return S3Storage(config,verify=verify) if config.USE_S3 else LocalStorage()

def get_samples_limits_paths(config):
    path=config.OBJECT_PREFIX
    sample_path=path+'/Sample.json'
    limit_path=path+'/Limit.json'
    return sample_path, limit_path

def get_conditions_paths(config):
    path=config.OBJECT_PREFIX
    return path+'/Conditions.json'

def get_samples_limits(config):
    sample_path, limit_path=get_samples_limits_paths(config)

    storage=get_storage(config)
    assert storage.exists(sample_path), 'Sample.json not found'
    assert storage.exists(limit_path), 'Limit.json not found'
    with storage.open(sample_path,'r') as f:
        samples=json.load(f)
    with storage.open(limit_path,'r') as f:
        limits=json.load(f)
    return samples,limits

def get_urgency_priorities(limits):
    urgencies=[]
    for limit in limits:
        level_key=([key for key in limit.keys() if 'level' in key.lower()]+[None])[0]
        if level_key is not None:
            limit_levels=limit[level_key]
            for x in limit_levels:
                x['upperlower']=np.nanmax([x.get('Upper',np.nan), x.get('upper',np.nan), -x.get('Lower',np.nan), -x.get('lower',np.nan)])
            limit_levels=sorted([x for x in limit_levels if x['upperlower'] is not None],key=lambda x: x['upperlower'])

            for limitlevel in limit_levels:
                cur_urgency=limitlevel.get('Urgency') or limitlevel.get('urgency')
                if cur_urgency is not None and cur_urgency.lower() not in urgencies:
                    urgencies.append(cur_urgency.lower())
    return urgencies

def get_equipment_limits(equipment_id,limits,property_name):
    levels=dict(upper=[],lower=[],urgency=[])
    for limit in limits:
        limit_equipment=limit.get('Equipment') or limit.get('equipment')
        if type(limit_equipment) not in [list,tuple,np.ndarray]:
            limit_equipment=[limit_equipment]
        if limit_equipment is None or equipment_id in limit_equipment:
            prop = limit.get('Property') or limit.get('property')
            level_key=([key for key in limit.keys() if 'level' in key.lower()]+[None])[0]
            if prop is not None and level_key is not None and prop.lower()==property_name.lower():
                for limitlevel in limit[level_key]:
                    levels['upper'].append(limitlevel['Upper'] if 'Upper' in limitlevel else (limitlevel['upper'] if 'upper' in limitlevel else np.inf))
                    levels['lower'].append(limitlevel['Lower'] if 'Lower' in limitlevel else (limitlevel['lower'] if 'lower' in limitlevel else -np.inf))
                    levels['urgency'].append(limitlevel.get('Urgency') or limitlevel.get('urgency'))
    return {key:np.array(vals) for key,vals in levels.items()}

def predict(config,samples,limits):
    #Loop through samples
    cur_t=0;cur_urgency=None;cur_sample=None
    conditions=[]
    ordered_urgencies=get_urgency_priorities(limits)
    conditions=[]
    for sample in samples:
        sample_equipment=sample.get('Equipment') or sample.get('equipment')
        if type(sample_equipment) not in [list,tuple,np.ndarray]:
            sample_equipment=[sample_equipment]
        data = sample.get('Data') or sample.get('data')

        if data:
            for property_name, values in data.items():
                t,y=zip(*[(x['t'],x['y']) for x in sorted(values,key=lambda x: x['t'])])
                y=np.array(y)
                t=np.array(t)

                for equipment_id in sample_equipment:
                    equipment_limits = get_equipment_limits(equipment_id,limits,property_name)
                    y_upper=y-equipment_limits['upper'].reshape((-1,1))
                    y_lower=equipment_limits['lower'].reshape((-1,1))-y
                    y_all=np.vstack([y_upper,y_lower])
                    y_all=np.where(np.logical_or(np.isnan(y_all),y_all<0),np.inf,y_all)
                    pos=~np.all(np.isinf(y_all),axis=0)
                    ind=np.argmin(y_all,axis=0)
                    urgency=np.tile(equipment_limits['urgency'],2)
                    cur_conditions=np.where(pos,urgency[ind],None)

                    prev_cond=None
                    for t,condition in zip(t[pos],urgency[ind][pos]):
                        if prev_cond is None or condition!=prev_cond:
                            conditions.append({
                                'Equipment_id':equipment_id,
                                'Property':property_name,
                                'Sample':sample['_id'],
                                'Condition':condition,
                                'Timestamp':t,
                                'Version':config.VERSION,
                                'Extra':(config.EXTRA_RETURN_ARGS if config.EXTRA_RETURN_ARGS else {}),
                            })
                            prev_cond=condition
    #Clean up
    conditions=sorted(conditions,key=lambda x: x['Timestamp'])
    res=[]
    for condition in conditions:
        prev_cond=[x for x in res if x['Timestamp']<=condition['Timestamp'] and x['Equipment_id']<=condition['Equipment_id']]
        if len(prev_cond)==0 or (condition['Property']==prev_cond[-1]['Property'] and condition['Condition']!=prev_cond[-1]['Condition']) or (condition['Property']!=prev_cond[-1]['Property'] and ordered_urgencies.index(condition['Condition'].lower())>ordered_urgencies.index(prev_cond[-1]['Condition'].lower())):
            res.append(condition)
    return res

def run_algorithm(config):
    samples,limits=get_samples_limits(config)
    conditions=predict(config,samples,limits)

    if config.RETURN_METHOD=='storage':
        storage=get_storage(config)
        path=config.OBJECT_PREFIX
        conditions_path=get_conditions_paths(config)
        storage.save(conditions_path,json.dumps(conditions))
        logger.info("Condition results stored as '%s'", conditions_path)
    elif config.RETURN_METHOD=='api':
        res=requests.post(config.API_URL, json=conditions, auth=(config.API_USERNAME, config.API_PASSWORD))
        logfcn=logger.info if res.status_code==200 else logger.exception
        try:
            msg=json.dumps(res.json(),indent=2)
        except:
            msg=res.text
        logfcn("Posting condition results to '%s' retured a '%i' status with content:\n'%s'",config.API_URL,res.status_code,msg)
    if config.DELETE_AFTER_COMPLETION:
        sample_path, limit_path=get_samples_limits_paths(config)
        storage=get_storage(config)
        storage.delete(sample_path)
        storage.delete(limit_path)
        logger.info("Deleted '%s' and '%s'", sample_path,limit_path)
