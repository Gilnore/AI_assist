# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 15:25:43 2024

@author: robin

you can reset everything by deleting the agent configs in agent repo
deleting everything in vector database
emptying the ai team config file
then calling project status tracker as False
"""
import autogen
# from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
# from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import sys
import os
import gc
import memory_data_management as mdm
from dotenv import load_dotenv
from construct_agent import construct_agent
from construct_skill import construct_skill
from project_status_tracker import project_status_tracker
from get_skill import get_skill
from assign_skill import assign_skill
from dump_summary import dump_summary
model_config = autogen.config_list_from_json("OAI_CONFIG_LIST.json",
                            file_location="E:\\AI_assist\\AI_assist\\")
base_llm_config = {"config_list":model_config,
              "timeout":60}
def restart()->None:
    gc.collect()
    os.execv(__file__, sys.argv)

def initiate_new_agents():
    with open('AI_team_config.txt') as team_config:
        m = mdm.mem(name = 'agents')
        team_names = team_config.readlines()
    agents = []
    #generate a list of agents
    load_dotenv()
    agents_config_path = os.getenv('agents')
    for name in team_names:
        name = name.strip()
        agent_meta = m.query(name)[0].payload.get('metadata')
        m.client.close()
        del m
        agent_tool_name_path = f"{agents_config_path}\\"
        function_config = autogen.config_list_from_json(f'{name}.json',
                                    file_location=agent_tool_name_path)
        llm_config = {"config_list":model_config,
                      "timeout":60,
                      'tools':function_config}
        new_ag = autogen.AssistantAgent(name = agent_meta.get('name'),
                               system_message= agent_meta.get('system_message'),
                               llm_config=llm_config)

        agents.append(new_ag)
    return agents

# we need to asigne agents tools, only dev can construct,
# everyone else can get and assigne for self, 
# planer can asign for others

code_tester = autogen.UserProxyAgent(name="code_tester",
    system_message="""
    your name is code_tester
    you are a code tester and test the codes that were given to you and return any error.
    you will execute any code given, debug if necessary.
    if you were hit with an error, explain step by step what the error means, 
    and propose how to fix the error.
    you are to give the original code, error and advice back to the agent named code_dev.
    code_dev is not a function to be called,
    code_planner is not a function to be called,
    none of the agents are functions to be called.
    """,
    llm_config = base_llm_config,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir":"code_execution_folder", "use_docker":False}
    )

#this dude plans steps to acheive any goal
task_planner = autogen.ConversableAgent(name= "task_planner",
    llm_config = base_llm_config,
    system_message="""
    your name is task_planner
    you are a planer with great forsight. 
    you come up with executable plans for a required goal.
    Revise the plan based on feedback from critic, until admin approval.
    your plans should be designed with collaboration in mind, 
    and each planned task should be clear enough to be understood by other departments.
    if you need more departments, 
    you can recruite new agents by using the construct_agent skill,
    the agent descriptions should be generalizable to suite a type of task,
    instead of to do a specific one.
    you can get existing skills names from their descriptions.
    you can assign other agents specific existing functions to use.
    you can request new functions to be made by asking the agent named code_planner.
    your request should be specific, the function should accomplish a specific task.
    you should send requests one at a time, 
    when it is ready, you can find them like other existing skills.
    you can not interact directly with the agent named code_dev.
    you must tell the secretary to memorize anything useful and restart the chat upon gaining a new agent or skill.
    do as much as you can without bothering the admin.
    your plans should be approved first by the agent named Critic before anything is done.
    code_dev is not a function to be called,
    code_planner is not a function to be called,
    none of the agents are functions to be called.
    """
    )
critic = autogen.AssistantAgent(
    name="Critic",
    system_message="""Critic. Double check plan, claims, code from other agents 
    and provide feedback.
    Check whether the plan includes adding verifiable info such as source URL.
    You can not execute any actions yourself asside pointing out errors of others.
    You can not code, nor look up anything, or apporve any plans.
    you can not interact directly with the agent named code_dev.
    code_dev is not a function to be called,
    code_planner is not a function to be called,
    task_planner is not a function to be called,
    none of the agents are functions to be called.
    """,
    llm_config= base_llm_config,
)
autogen.agentchat.register_function(construct_agent,
    caller=task_planner,
    executor=code_tester,
    description="""find a existing agent using its description, 
    if the agent cant be found it returns None""")


autogen.agentchat.register_function(get_skill,
    caller=task_planner,
    executor=code_tester,
    description="""find a existing function using its description,
    if the function cant be found it returns None""")

autogen.agentchat.register_function(assign_skill,
    caller=task_planner,
    executor=code_tester,
    description="""assign an existing skill to other agents on your team, 
    you can only use this on existing skills or it will error out""")
    
#this dude plans the code to acheive steps in the task plan
code_planner = autogen.ConversableAgent(name = 'code_planner',
    llm_config = base_llm_config,
    system_message="""
    your name is code_planner
    you plan code in a step by step way based on directives given to you.
    if you are given a plan already, break it up to the fundamental steps and plan code for each.
    you will then give the plans to the agent named code_dev for detailed implementation.
    your plans should be detailed and cover even edge cases.
    you should conduct research if necessary.
    
    you can also construct skills coded by code_dev for other agents.
    you must plan out the skill for it to be written by code_dev,
    only after code_dev and code_tester finish testing and developing can you save it.
    use construct_skill function to save code.
    you should ensure there are no duplicate skills, 
    if there are you must decide to either rename the new skill or to overwrite the existing.
    your plans should be approved first by the agents task_planner and Critic before anything is done.
    """
    )

autogen.agentchat.register_function(construct_skill,
    caller=code_planner,
    executor=code_tester,
    description="""create a new skill and add it to skill database,
    you should ensure there are no duplicate skills, 
    if there are you must decide to either rename the new skill or to overwrite the existing.
    """)
#this is the actual programer
code_dev = autogen.AssistantAgent(name = 'code_dev',
    llm_config = base_llm_config,
    system_message="""
    your name is code_dev
    you are responsible for implementing the features demanded by the agent named code_planner in python code.
    the codes need to be well documented and easy to read.
    you are to give the finished code to the agent named code_planer to check that it is in accrodence with demand.
    you must check your code by the agent named critic first.
    you must test and run code by giveing the code to the agent named code_tester.
    you are to return the code to the agent named code_planner when and only when everything works fine.
    The user can't modify your code. 
    So do not suggest incomplete code which requires others to modify.
    Don't use a code block if it's not intended to be executed by the the agent named code_tester.
    Don't include multiple code blocks in one response. 
    Do not ask others to copy and paste the result. 
    Check the execution result returned by the the agent named code_tester.
    If the result indicates there is an error, fix the error and output the code again. 
    Suggest the full code instead of partial code or code changes. 
    If the error can't be fixed or if the task is not solved even after the code is executed successfully, 
    analyze the problem, revisit your assumption, collect additional info you need, 
    and think of a different approach to try.
    code_dev is not a function to be called,
    code_planner is not a function to be called,
    task_planner is not a function to be called,
    none of the agents are functions to be called.
    """
    )

#we need someone to plan for what to get, and get them, likly used in skill lib
#this peroson keeps track of chat history and todo lists, and injects it into chat upon restart
#
secretary = autogen.ConversableAgent(name = 'secretary',
    llm_config= base_llm_config,
    system_message="""
    your name is secretary,
    you keep track of the conversation and memorize things that needs to be done as a todo list,
    you are responsible for reminding other agents of what still need to be done.
    you are responsible for restarting the entire program after new members join or after people gains more skills.
    you are to recorde if the project was complete or is it still on going
    any restarts should be approved first by the agent named task planner before anything is done.
    you can not interact directly with the agent named code_dev.
    you can restart the program by using the restart function
    code_dev is not a function to be called,
    code_planner is not a function to be called,
    task_planner is not a function to be called,
    none of the agents are functions to be called.
    """)
autogen.agentchat.register_function(project_status_tracker,
    caller=secretary,
    executor=code_tester,
    description="""tracks project status, False if new project, True if on going.""")
autogen.agentchat.register_function(restart,
    caller=secretary,
    executor=code_tester,
    description="""restart the program to update the team or update skills the team have.""")
autogen.agentchat.register_function(dump_summary, 
    caller = secretary, 
    executor = code_tester,
    description ="dump the todo list and key summary of the conversations here")

user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message="""A human admin. Interact with the planner to discuss the plan. 
    Plan execution needs to be approved by this admin.""",
    code_execution_config=False,
)
agents = [code_dev,code_tester,code_planner,task_planner,secretary,user_proxy,critic] \
    + initiate_new_agents()
with open('project_status.txt') as status_file:
    status = status_file.readline()

groupchat = autogen.GroupChat(agents=agents, messages=[], max_round=50)
manager = autogen.GroupChatManager(groupchat=groupchat,llm_config=base_llm_config)
summary = ''
summary_path = os.getenv('logs')+'\\session_summary.txt'
if status == 'finish where we left off last time.':
    with open(summary_path) as summary_file:
        summary = summary_file.read()
messages = input('what can we help you with?\n')
# messages = 'find me a youtube video on day trading and give a summary of its transcripts.'

user_proxy.initiate_chat(
    manager,
    message= f"""
    {messages} 
    
   status of project: {status}
   
   summary and todo from last time: {summary}"""
)



# print('task complete, dumping logs')
#we need code to dump logs to folder