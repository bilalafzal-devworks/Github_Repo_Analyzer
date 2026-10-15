from crewai import Agent, Task
from tools import github_repo_info, read_repo_file

NAME = "Repo Scanner"
ICON = "🔍"
ROLE = "GitHub Repository Inspector"

def build(llm, repo_url: str, github_token: str = "", depth_config: dict = None):
    agent = Agent(
        role="GitHub Repository Inspector",
        goal="Extract comprehensive metadata, file structure, languages, commits, and existing README content from the target GitHub repository.",
        backstory="Expert code archaeologist specialized in rapidly parsing and indexing public GitHub codebases.",
        tools=[github_repo_info, read_repo_file],
        llm=llm,
        verbose=True,
        max_iter=depth_config.get("max_iter", 4) if depth_config else 4
    )
    
    task = Task(
        name=NAME,
        description=f"Scan the public GitHub repository at {repo_url} using github_repo_info and read_repo_file if needed. Extract metadata, file structure, primary language, recent commits, and existing documentation. Output a structured repository summary.",
        expected_output="A structured summary of repository metadata, languages, file structure, and recent activity.",
        agent=agent
    )
    return agent, task