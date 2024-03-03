# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 23:42:42 2024

@author: robin
"""
import memory_data_management as mdm
def get_agent(description:str)->dict:
    """retreive agent information from its description, 
    you can use this to find if there are anyone you want"""
    m = mdm.mem(name = 'agents')
    ag = m.query(description, 
            query_instruction="represent this job description for later retreival.")
    if ag[0].score > 0.8 and ag[0].payload.get('metadata') is not None:
        return ag[0].payload.get('metadata')
    else:
        return None