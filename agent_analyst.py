from crewai import Agent, Task
from tools import web_search, read_repo_file

NAME = "Tech-Stack Analyst"
ICON = "⚙️"
ROLE = "Technology & Architecture Evaluator"

def build(llm, repo_url: str, github_token: str = "", depth_config: dict = None):
    max_words = depth_config.get("max_words_analysis", 600) if depth_config else 600
    agent = Agent(
        role="Technology & Architecture Evaluator",
        goal="Analyze the repository tech stack, software architecture, strengths, and engineering gaps (tests, docs, setup steps).",
        backstory="Senior software architect skilled at evaluating code quality, identifying dependencies, and spotting architectural strengths and gaps.",
        tools=[web_search, read_repo_file],
        llm=llm,
        verbose=True,
        max_iter=depth_config.get("max_iter", 4) if depth_config else 4
    )
    
    task = Task(
        name=NAME,
        description=f"Analyze the tech stack and architecture of repository {repo_url} based on the scanner notes. Identify libraries, frameworks, setup steps, architectural strengths, and missing gaps (e.g., tests, documentation). Keep the response under {max_words} words.",
        expected_output=f"A thorough tech stack and architecture analysis under {max_words} words.",
        agent=agent
    )
    return agent, task