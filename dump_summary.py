# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 22:07:08 2024

@author: robin
"""
import os
from dotenv import load_dotenv
def dump_summary(session_summary:str)->None:
    load_dotenv()
    log_path = os.getenv('logs')
    with open(log_path+'\\session_summary.txt','w+') as summary_file:
        summary_file.write(session_summary)