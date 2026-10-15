from crewai import Agent, Task
from tools import check_links

NAME = "README Writer"
ICON = "📝"
ROLE = "Professional Technical Writer"

def build(llm, repo_url: str, github_token: str = "", depth_config: dict = None):
    max_words = depth_config.get("max_words_readme", 1200) if depth_config else 1200
    agent = Agent(
        role="Professional Technical Writer",
        goal="Draft a comprehensive, professional, production-ready README.md file with verified links and clear installation guides.",
        backstory="World-class technical writer who creates stellar, easy-to-read open source documentation that drives project adoption.",
        tools=[check_links],
        llm=llm,
        verbose=True,
        max_iter=depth_config.get("max_iter", 4) if depth_config else 4
    )
    
    task = Task(
        name=NAME,
        description=f"Using the repository analysis and tech stack notes for {repo_url}, write a professional, production-ready README.md including Title, Description, Features, Tech Stack, Installation Guide, Usage, and License. Validate any included URLs with check_links. Keep the response under {max_words} words.",
        expected_output=f"A complete, markdown-formatted README.md under {max_words} words.",
        agent=agent
    )
    return agent, task