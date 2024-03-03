# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 02:30:00 2024

@author: robin
"""
# import importlib as imp
from dotenv import load_dotenv
# import os
import memory_data_management as mdm

def get_skill(description:str)->str:
    """this function finds and grabs a function best fitting for the description"""
    load_dotenv()
    m = mdm.mem(name='functions') #make memory manager
    similar_results = m.query(description,
                              query_instruction='represent this description of a python function',
                              limit=1)
    m.client.close()
    del m
    valid_results = [point.payload.get('metadata').get('name') for point in similar_results if point.score > 0.8]
    all_nones = all([results==None for results in valid_results])
    if valid_results == [] or all_nones:
        print('no such a skill exist yet, you need to program one in python')
        return None
    else:
        name = valid_results[0]
        # function_folder = os.getenv('functions')
        # func = getattr(imp.import_module(f"{function_folder}.{name}"),name)
    return name

