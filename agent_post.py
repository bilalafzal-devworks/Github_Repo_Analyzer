from crewai import Agent, Task
from tools import check_post_length

NAME = "LinkedIn Post Writer"
ICON = "🚀"
ROLE = "Social Media Growth Specialist"

def build(llm, repo_url: str, github_token: str = "", depth_config: dict = None):
    max_words = depth_config.get("max_words_post", 400) if depth_config else 400
    agent = Agent(
        role="Social Media Growth Specialist",
        goal="Craft an engaging, ready-to-post LinkedIn launch announcement that highlights the repo's value and invites community feedback.",
        backstory="Growth marketer specialized in tech launches, viral hooks, and developer community engagement on LinkedIn.",
        tools=[check_post_length],
        llm=llm,
        verbose=True,
        max_iter=depth_config.get("max_iter", 4) if depth_config else 4
    )
    
    task = Task(
        name=NAME,
        description=f"Draft a ready-to-post LinkedIn launch announcement for repository {repo_url} highlighting key features and inviting feedback. Verify the length using check_post_length to ensure it is strictly under 3,000 characters and around {max_words} words.",
        expected_output=f"A polished, engaging LinkedIn announcement under {max_words} words.",
        agent=agent
    )
    return agent, task