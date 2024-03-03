# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 21:05:12 2024

@author: robin
"""
def project_status_tracker(on_going:bool)->None:
    if on_going:
        with open('project_status.txt','w+') as status:
            status.write('finish where we left off last time.')
    else:
        with open('project_status.txt','w+') as status:
            status.write('starting the new project.')