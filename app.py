import time
import queue
import threading
import streamlit as st

import agent_scanner
import agent_analyst
import agent_readme
import agent_post
from crew import run_repo_crew

st.set_page_config(
    page_title="GitHub Repo Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .hero-header {
        background: linear-gradient(135deg, #4f46e5 0%, #ec4899 100%);
        padding: 36px 40px;
        border-radius: 20px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(236, 72, 153, 0.3);
    }
    .hero-header h1 {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .hero-header p {
        font-size: 18px;
        opacity: 0.9;
        margin: 0;
    }
    .agent-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #ec4899 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

groq_key = ""
try:
    if "GROQ_API_KEY" in st.secrets:
        groq_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not groq_key:
    import os
    groq_key = os.environ.get("GROQ_API_KEY", "")

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    repo_url = st.text_input("Public GitHub Repo URL", placeholder="https://github.com/owner/repo")
    github_token = st.text_input("GitHub Token (Optional)", type="password", placeholder="ghp_xxxxxxxxxxxx")
    depth_level = st.selectbox("Analysis Depth", ["Quick", "Standard", "Deep"], index=1)
    
    st.markdown("---")
    st.markdown("### 🤖 Agent Team")
    st.markdown(f"- **{agent_scanner.ICON} {agent_scanner.NAME}**")
    st.markdown(f"- **{agent_analyst.ICON} {agent_analyst.NAME}**")
    st.markdown(f"- **{agent_readme.ICON} {agent_readme.NAME}**")
    st.markdown(f"- **{agent_post.ICON} {agent_post.NAME}**")
    
    st.markdown("---")
    run_clicked = st.button("🚀 Analyze Repository")

st.markdown("""
<div class="hero-header">
    <h1>GitHub Repo Analyzer</h1>
    <p>Autonomous AI Agent Pipeline for Instant Project Analysis, Professional READMEs & Viral Launch Posts</p>
</div>
""", unsafe_allow_html=True)

if not groq_key:
    st.warning("⚠️ **GROQ_API_KEY not found.** Please add your Groq API key in Streamlit Secrets (`.streamlit/secrets.toml`) or as an environment variable to run the analysis.")

if run_clicked:
    if not groq_key:
        st.error("Cannot run without GROQ_API_KEY.")
    elif not repo_url or "github.com" not in repo_url:
        st.error("Please enter a valid public GitHub repository URL.")
    else:
        q = queue.Queue()
        
        status_banner = st.empty()
        timer_placeholder = st.empty()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            c1_box = st.empty()
        with col2:
            c2_box = st.empty()
        with col3:
            c3_box = st.empty()
        with col4:
            c4_box = st.empty()
            
        tool_feed_expander = st.expander("🛠️ Live Tool Call Feed", expanded=True)
        tool_feed_container = tool_feed_expander.empty()
        
        def render_agent_status(active_idx):
            statuses = ["Waiting", "Waiting", "Waiting", "Waiting"]
            if active_idx < 4:
                statuses[active_idx] = "Working now ⚡"
            for i in range(active_idx):
                statuses[i] = "Done ✅"
                
            agents_info = [
                (agent_scanner.ICON, agent_scanner.NAME),
                (agent_analyst.ICON, agent_analyst.NAME),
                (agent_readme.ICON, agent_readme.NAME),
                (agent_post.ICON, agent_post.NAME)
            ]
            
            for idx, box in enumerate([c1_box, c2_box, c3_box, c4_box]):
                icon, name = agents_info[idx]
                st_text = statuses[idx]
                box.markdown(f"""
                <div class="agent-card">
                    <h4>{icon} {name}</h4>
                    <p style="margin:4px 0 0 0; font-size:14px; color:{'#38bdf8' if 'Working' in st_text else ('#4ade80' if 'Done' in st_text else '#94a3b8')}"><b>{st_text}</b></p>
                </div>
                """, unsafe_allow_html=True)

        render_agent_status(0)
        status_banner.info("Initializing multi-agent crew pipeline...")
        
        t = threading.Thread(target=run_repo_crew, args=(repo_url, groq_key, github_token, depth_level, q))
        t.start()
        
        start_time = time.time()
        tool_logs = []
        current_agent_idx = 0
        final_results = None
        error_msg = None
        
        while t.is_alive() or not q.empty():
            elapsed = int(time.time() - start_time)
            timer_placeholder.markdown(f"⏱️ **Elapsed Time:** {elapsed}s | **Active Agent:** {[agent_scanner.NAME, agent_analyst.NAME, agent_readme.NAME, agent_post.NAME][current_agent_idx]}")
            
            try:
                msg_type, msg_content = q.get(timeout=0.2)
                if msg_type == "tool":
                    tool_logs.append(msg_content)
                    tool_feed_container.code("\n".join(tool_logs[-8:]))
                elif msg_type == "status":
                    status_banner.info(msg_content)
                    if "Tech-Stack Analyst" in msg_content or "Analyst" in msg_content:
                        current_agent_idx = 1
                        render_agent_status(1)
                    elif "README" in msg_content:
                        current_agent_idx = 2
                        render_agent_status(2)
                    elif "LinkedIn" in msg_content or "Post" in msg_content:
                        current_agent_idx = 3
                        render_agent_status(3)
                elif msg_type == "complete":
                    final_results = msg_content
                    render_agent_status(4)
                elif msg_type == "error":
                    error_msg = msg_content
            except queue.Empty:
                pass
                
        t.join()
        
        if error_msg:
            st.error(f"❌ Error during execution: {error_msg}")
        elif final_results:
            status_banner.success("✨ Multi-agent analysis complete successfully!")
            
            tab1, tab2, tab3 = st.tabs(["📊 Project Analysis", "📝 README.md", "🚀 LinkedIn Post"])
            
            with tab1:
                st.markdown("### Project Analysis & Tech Stack Evaluation")
                analysis_text = final_results.get("analysis", "No analysis generated.")
                st.markdown(analysis_text)
                st.download_button("📥 Download Analysis", analysis_text, file_name="repo_analysis.md", mime="text/markdown")
                
            with tab2:
                st.markdown("### Professional README.md")
                readme_text = final_results.get("readme", "No README generated.")
                st.code(readme_text, language="markdown")
                st.download_button("📥 Download README.md", readme_text, file_name="README.md", mime="text/markdown")
                
            with tab3:
                st.markdown("### LinkedIn Launch Announcement")
                post_text = final_results.get("post", "No post generated.")
                st.text_area("Post Preview", post_text, height=250)
                st.download_button("📥 Download LinkedIn Post", post_text, file_name="linkedin_post.txt", mime="text/markdown")
