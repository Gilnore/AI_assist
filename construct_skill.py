# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 23:12:44 2024

@author: robin
"""
from dotenv import load_dotenv
import os
import memory_data_management as mdm
import openai
from aider.coders import Coder
# import importlib as imp
# from get_skill import get_skill
def construct_skill(description:str, name:str, code:str, overwrite:bool=False, use_aider:bool = False)->None:
    """register a function from description, save its code at a set path with a said name.
    
    """
    load_dotenv()
    # function_folder = os.getenv('functions')
    #create the file for storing code
    function_repo_path = os.getenv('functions_folder') + '\\'+name +'.py'
    if os.path.exists(function_repo_path) and not overwrite:
        raise ValueError('existing function detected')
    else:
        m = mdm.mem(name='functions') #make memory manager
        with open(function_repo_path,'w+') as func_file:
            func_file.write(code)
        if use_aider:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            coder = Coder.create(client=client, fnames=[function_repo_path])
            coder.run("""check that the code written acheives the following purpose
                      {description}
                      ensure that the function is named with {name}
                      think through the code step by step and hammer out any bugs.
                      """)
        #we need to print code to the message lst to be reconized
        #that would be taken care at agent level, if that doesn't work then try hard code it
        function_metadata = {'name':name,'description':description,'code':code}
        m.perm_mem(name + '\n: ' + description,
                   meta = function_metadata,
                   embed_instruction="represent this python function description for later retreival.")
        m.client.close()
        del m

