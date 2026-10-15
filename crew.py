from dataclasses import dataclass
import agent_scanner
import agent_analyst
import agent_readme
import agent_post
from config import DEPTH_SETTINGS
from crewai import Crew, LLM

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

def run_crew(repo_url, depth_level, groq_api_key, event_callback, model_override=None):
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
    
    event_callback("agent_start", 0)
    result = crew.kickoff()
    output_text = str(result)
    
    output_dict = f"""
## 📊 Project Analysis & Tech Stack Evaluation
{output_text}

---

## 📝 Professional README.md
```markdown
{output_text}
