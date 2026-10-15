# GitHub Repo Analyzer

An autonomous 4-agent AI application built with **CrewAI**, **Streamlit**, and **Groq** that takes any public GitHub repository link and generates:
1. A comprehensive project analysis
2. A professional, production-ready `README.md`
3. A ready-to-post LinkedIn launch announcement

## Tech Stack
- **Orchestration:** CrewAI (`crewai==1.15.28`)
- **UI:** Streamlit (`streamlit==1.65.0`)
- **LLM:** Groq (`openai/gpt-oss-120b` via OpenAI provider format)
- **Search & HTTP:** `ddgs==9.16.0`, `httpx==0.28.1`, `beautifulsoup4==4.15.0`