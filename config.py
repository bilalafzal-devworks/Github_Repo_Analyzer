# Configuration and Depth Settings for GitHub Repo Analyzer

DEPTH_SETTINGS = {
    "Quick": {
        "max_tool_calls": 3,
        "max_iter": 2,
        "max_words_analysis": 300,
        "max_words_readme": 600,
        "max_words_post": 250,
    },
    "Standard": {
        "max_tool_calls": 6,
        "max_iter": 4,
        "max_words_analysis": 600,
        "max_words_readme": 1200,
        "max_words_post": 400,
    },
    "Deep": {
        "max_tool_calls": 10,
        "max_iter": 6,
        "max_words_analysis": 1000,
        "max_words_readme": 2000,
        "max_words_post": 600,
    }
}