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

def predict(config,samples,limits):
    #Get Counts limits
    levels=[(-1,'Healthy')]
    for limit in limits:
        if 'Property' in limit and limit['Property']=='Counts' and 'LimitLevel' in limit:
            for limitlevel in limit['LimitLevel']:
                levels.append((limitlevel['Upper'],limitlevel['Urgency']))
    levels=sorted(levels,key=lambda x: x[0])
    def get_value_urgency(val):
        for level in levels:
            if val>=level[0]:
                return level[1]
    #Loop through samples
    cur_t=0;cur_urgency=None;cur_sample=None
    conditions=[]
    for sample in samples:
        if 'Data' in sample and 'Counts' in sample['Data']:
            counts=sample['Data']['Counts']
            counts=sorted(counts,key=lambda x: x['t'])
            t=[];y=[]
            for ty in counts:
                t.append(ty['t'])
                y.append(ty['y'])
            t=np.array(t); y=np.array(y)
            for level in levels:
                pos_ts=np.where(y>=level[0])[0]
                if len(pos_ts)>0:
                    pos=pos_ts[0]
                    if sample['_id']!=cur_sample or (t[pos]>cur_t and level[1]!=cur_urgency):
                        cur_t=t[pos]
                        cur_urgency=level[1]
                        cur_sample=sample['_id']
                        conditions.append({
                                            'Sample':cur_sample,
                                            'Condition':cur_urgency,
                                            'Timestamp':cur_t,
                                            'Version':config.VERSION,
                                        })
                        if config.EXTRA_RETURN_ARGS:
                            conditions[-1]['Extra']=config.EXTRA_RETURN_ARGS
    return conditions

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
