from dataclasses import dataclass
from queue import Queue
from crewai import Crew, LLM, Task
from crewai.events import crewai_event_bus
from crewai.events.types.tool_usage_events import ToolUsageStartedEvent

import agent_scanner
import agent_analyst
import agent_readme
import agent_post
from config import DEPTH_SETTINGS

@dataclass
class AgentMeta:
    NAME: str
    ICON: str
    ROLE: str

TEAM = [
    AgentMeta(agent_scanner.NAME, agent_scanner.ICON, agent_scanner.ROLE),
    AgentMeta(agent_analyst.NAME, agent_analyst.ICON, agent_analyst.ROLE),
    AgentMeta(agent_readme.NAME, agent_readme.ICON, agent_readme.ROLE),
    AgentMeta(agent_post.NAME, agent_post.ICON, agent_post.ROLE),
]

def run_crew(repo_url: str, depth_level: str, groq_api_key: str, event_callback, model_override: str = None) -> str:
    depth_config = DEPTH_SETTINGS.get(depth_level, DEPTH_SETTINGS["Standard"])
    model_name = model_override or "openai/gpt-oss-120b"
    
    llm_standard = LLM(
        model=model_name,
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
        model=model_name,
        provider="openai",
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key,
        temperature=0.3,
        max_tokens=3000,
        reasoning_effort="low",
        timeout=120,
        max_retries=6
    )
    
    agent1, task1 = agent_scanner.build(llm_standard, repo_url, "", depth_config)
    agent2, task2 = agent_analyst.build(llm_standard, repo_url, "", depth_config)
    agent3, task3 = agent_readme.build(llm_writer, repo_url, "", depth_config)
    agent4, task4 = agent_post.build(llm_writer, repo_url, "", depth_config)
    
    crew = Crew(
        agents=[agent1, agent2, agent3, agent4],
        tasks=[task1, task2, task3, task4],
        verbose=True
    )
    
    @crewai_event_bus.scoped_handlers()
    def handle_tool_start(event: ToolUsageStartedEvent):
        tool_name = getattr(event, "tool_name", "unknown_tool")
        event_callback("tool", (0, tool_name))
        
    event_callback("agent_start", 0)
    
    result = crew.kickoff()
    
    event_callback("agent_done", 0)
    event_callback("agent_start", 1)
    event_callback("agent_done", 1)
    event_callback("agent_start", 2)
    event_callback("agent_done", 2)
    event_callback("agent_start", 3)
    event_callback("agent_done", 3)
    
    output_dict = f"""
## 📊 Project Analysis & Tech Stack Evaluation
{getattr(task2, 'output', 'Analysis generated.')}

---

## 📝 Professional README.md
```markdown
{getattr(task3, 'output', 'README generated.')}
