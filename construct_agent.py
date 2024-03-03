# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 19:23:47 2024

@author: robin
"""
from dotenv import load_dotenv
import os
import memory_data_management as mdm
from get_agent import get_agent
def construct_agent(responsibilities:str,name_of_agent:str)->dict:
    """create an entry for a agent with specialized responsibilities
    """
    load_dotenv()
    agents_config_path = os.getenv('agents')
    agent_tool_name_path = f"{agents_config_path}\\{name_of_agent}.json"
    if os.path.exists(agent_tool_name_path):
        print('existing function detected')
        return get_agent(responsibilities)
    else:
        with open(agent_tool_name_path,'w+') as tool_config:
            tool_config.write('[]')
        with open('AI_team_config.txt','a') as team_config:
            team_config.write(name_of_agent+'\n')
        message = f"""your name is {name_of_agent}, you have the following job:
                            {responsibilities}"""
        agent_metadata = {'name':name_of_agent,
                          'system_message':message,
                          'tools_names_path':agent_tool_name_path}
        m = mdm.mem(name='agents') #make memory manager
        m.perm_mem(message,
                   meta = agent_metadata,
                   embed_instruction="represent this job description for later retreival.")
        m.client.close()
        del m
        print('agent added to team, reload chat to apply.')
        return agent_metadata