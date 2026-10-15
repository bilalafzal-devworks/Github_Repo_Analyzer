import threading
from queue import Queue
from crewai import Crew, LLM
from crewai.events import crewai_event_bus
from crewai.events.types.tool_usage_events import ToolUsageStartedEvent

import agent_scanner
import agent_analyst
import agent_readme
import agent_post
from config import DEPTH_SETTINGS

def run_repo_crew(repo_url: str, groq_api_key: str, github_token: str, depth_level: str, event_queue: Queue):
    try:
        depth_config = DEPTH_SETTINGS.get(depth_level, DEPTH_SETTINGS["Standard"])
        
        llm_standard = LLM(
            model="openai/gpt-oss-120b",
            provider="openai",
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=1500,
            reasoning_effort="low",
            timeout=120,
            max_retries=6
        )
        
        llm_writer = LLM(
            model="openai/gpt-oss-120b",
            provider="openai",
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=3000,
            reasoning_effort="low",
            timeout=120,
            max_retries=6
        )
        
        agent1, task1 = agent_scanner.build(llm_standard, repo_url, github_token, depth_config)
        agent2, task2 = agent_analyst.build(llm_standard, repo_url, github_token, depth_config)
        agent3, task3 = agent_readme.build(llm_writer, repo_url, github_token, depth_config)
        agent4, task4 = agent_post.build(llm_writer, repo_url, github_token, depth_config)
        
        crew = Crew(
            agents=[agent1, agent2, agent3, agent4],
            tasks=[task1, task2, task3, task4],
            verbose=True
        )
        
        @crewai_event_bus.scoped_handlers()
        def handle_tool_start(event: ToolUsageStartedEvent):
            tool_name = getattr(event, "tool_name", "unknown_tool")
            event_queue.put(("tool", f"Tool called: {tool_name}"))
            
        event_queue.put(("status", "Starting Repo Scanner..."))
        
        result = crew.kickoff()
        output_str = str(result)
        
        event_queue.put(("complete", {
            "analysis": getattr(task2, "output", None) and str(task2.output) or output_str,
            "readme": getattr(task3, "output", None) and str(task3.output) or output_str,
            "post": getattr(task4, "output", None) and str(task4.output) or output_str,
            "raw": output_str
        }))
        
    except Exception as e:
        event_queue.put(("error", str(e)))
        
