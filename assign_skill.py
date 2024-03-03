# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 22:17:57 2024

@author: robin

not working yet, try dumping json
"""
from typing import List
import os
from dotenv import load_dotenv
from get_skill import get_skill
import autogen
import importlib as imp
def assign_skill(agent_name:str,function_description:str,function_name:str)->None:
    """we will load a existing skill to the targeted agent skill manifest"""
    load_dotenv()
    agents_config_path = os.getenv('agents')

    agent_tool_name_path = f"{agents_config_path}\\"
    #directly construct agent by loading in function descriptions in llm config
    model_config_list = autogen.config_list_from_json("OAI_CONFIG_LIST.json",
                            file_location="E:\\AI_assist\\AI_assist\\")
    function_config = autogen.config_list_from_json(f"{agent_name}.json",
                                    file_location=agent_tool_name_path)
    function_mod = os.getenv('functions')
    func = getattr(imp.import_module(f"{function_mod}.{function_name}"),function_name)
    #directly construct a blank userproxy for executor
    userproxy = autogen.UserProxyAgent(name='upa_place_holder',
                code_execution_config={"work_dir":"code_execution_folder", "use_docker":False})
    llm_config = {"config_list":model_config_list,
                  "request_timeout":60,
                  'function_map':function_config}
    assistant = autogen.AssistantAgent(name=agent_name,llm_config=llm_config)
    #register tool and dump json to the right path
    autogen.agentchat.register_function(func,
                                        caller=assistant,
                                        executor=userproxy,
                                        description=function_description)
    func_des = assistant.llm_config.get('tools')
    function_config = function_config + func_des
    with open(agent_tool_name_path+f"{agent_name}.json",'w') as conf:
        conf.write(str(function_config))