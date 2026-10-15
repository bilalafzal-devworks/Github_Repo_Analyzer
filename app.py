import os
import queue
import threading
import time
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="GitHub Repo Analyzer", page_icon="🤖", layout="wide")

try:
    from crew import TEAM, run_crew
except ImportError as exc:
    st.error(f"A project file is missing from your GitHub repo or is in the wrong place.\n\n`{exc}`")
    st.markdown(
        "The **main page** of your repo must list all of these files (no folders needed):\n\n"
        "`app.py` · `crew.py` · `config.py` · `tools.py` · `requirements.txt` · "
        "`agent_scanner.py` · `agent_analyst.py` · `agent_readme.py` · `agent_post.py`"
    )
    st.stop()

# ---------- Styling ----------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2rem; max-width: 1200px; }
.hero {
  padding: 2.2rem 2.4rem; border-radius: 24px; margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
  color: white; box-shadow: 0 20px 50px rgba(79,70,229,.30);
}
.hero h1 { margin: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -0.02em; }
.hero p { margin: .5rem 0 0; font-size: 1.05rem; opacity: .92; }
.badge {
  display: inline-block; padding: .25rem .8rem; margin: 1rem .4rem 0 0; border-radius: 999px;
  background: rgba(255,255,255,.18); font-size: .8rem; font-weight: 600;
  backdrop-filter: blur(6px); border: 1px solid rgba(255,255,255,.25);
}
.pipeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: .5rem 0 1.2rem; }
@media (max-width: 900px) { .pipeline { grid-template-columns: repeat(2, 1fr); } }
.agent {
  border-radius: 20px; padding: 1.2rem; border: 1.5px solid rgba(128,128,128,.25);
  background: rgba(128,128,128,.06); transition: all .3s ease; position: relative;
}
.agent .icon { font-size: 2rem; }
.agent .name { font-weight: 700; margin-top: .4rem; font-size: 1.02rem; }
.agent .role { font-size: .82rem; opacity: .7; margin-top: .15rem; min-height: 2.4em; }
.agent .state { margin-top: .7rem; font-size: .8rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
.agent.waiting { opacity: .55; }
.agent.working {
  border-color: #7c3aed; background: rgba(124,58,237,.12);
  box-shadow: 0 0 0 4px rgba(124,58,237,.15), 0 12px 30px rgba(124,58,237,.25);
  animation: pulse 1.6s ease-in-out infinite; transform: translateY(-3px);
}
.agent.working .state { color: #7c3aed; }
.agent.done { border-color: #10b981; background: rgba(16,185,129,.10); }
.agent.done .state { color: #10b981; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 4px rgba(124,58,237,.12), 0 12px 30px rgba(124,58,237,.2);}
                    50% { box-shadow: 0 0 0 9px rgba(124,58,237,.06), 0 16px 40px rgba(124,58,237,.35);} }
.now {
  padding: .9rem 1.2rem; border-radius: 14px; font-weight: 600;
  background: rgba(124,58,237,.10); border-left: 5px solid #7c3aed; margin-bottom: 1rem;
}
.feed { font-size: .88rem; line-height: 1.7; opacity: .9; }
.feed code { font-size: .8rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Header ----------
st.markdown(
    """
<div class="hero">
  <h1>🤖 GitHub Repo Analyzer</h1>
  <p>Autonomous 4-agent team inspects your repo, evaluates architecture, writes professional READMEs, and crafts launch posts.</p>
  <span class="badge">CrewAI</span><span class="badge">Groq · gpt-oss-120b</span>
  <span class="badge">GitHub REST API</span><span class="badge">4 AI Agents</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
def _get_api_key() -> str:
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        key = ""
    return (key or os.environ.get("GROQ_API_KEY", "")).strip()

api_key = _get_api_key()

with st.sidebar:
    st.header("⚙️ Settings")
    depth = st.select_slider("Analysis depth", ["Quick", "Standard", "Deep"], value="Standard")
    with st.expander("Advanced"):
        model = st.text_input(
            "Groq model",
            value="openai/gpt-oss-120b",
            help="Groq's free plan limits tokens per minute for each model.",
        )
    st.divider()
    st.markdown("**Your agent team**")
    for m in TEAM:
        st.markdown(f"{m.ICON} **{m.NAME}** \n<small>{m.ROLE}</small>", unsafe_allow_html=True)

# ---------- Helpers ----------
def pipeline_html(states: list[str]) -> str:
    labels = {"waiting": "⏳ Waiting", "working": "⚡ Working now", "done": "✅ Done"}
    cards = ""
    for m, s in zip(TEAM, states):
        cards += (
            f'<div class="agent {s}"><div class="icon">{m.ICON}</div>'
            f'<div class="name">{m.NAME}</div><div class="role">{m.ROLE}</div>'
            f'<div class="state">{labels[s]}</div></div>'
        )
    return f'<div class="pipeline">{cards}</div>'

# ---------- Main input ----------
repo_url = st.text_input(
    "Public GitHub Repository URL",
    placeholder="https://github.com/streamlit/streamlit",
)
go = st.button("🚀 Analyze Repository", type="primary", use_container_width=True)

pipeline_box = st.empty()
now_box = st.empty()
feed_box = st.empty()

if "report" not in st.session_state:
    st.session_state.report = None

if not go:
    pipeline_box.markdown(pipeline_html(["waiting"] * len(TEAM)), unsafe_allow_html=True)

# ---------- Run ----------
if go:
    if not api_key:
        st.error(
            "The Groq API key is not set. In Streamlit open **Manage app → Settings → Secrets**, "
            'add `GROQ_API_KEY = "gsk_your_key"`, save, then reboot the app.'
        )
        st.stop()
    if not repo_url.strip() or "github.com" not in repo_url:
        st.warning("Please enter a valid public GitHub repository URL.")
        st.stop()

    st.session_state.report = None
    events: queue.Queue = queue.Queue()
    states = ["waiting"] * len(TEAM)
    feed: list[str] = []

    def worker():
        try:
            text = run_crew(
                repo_url.strip(), depth, api_key, lambda k, p: events.put((k, p)), model.strip() or None
            )
            events.put(("finished", text))
        except Exception as exc:
            events.put(("error", str(exc)))

    threading.Thread(target=worker, daemon=True).start()

    def log(msg: str):
        feed.append(f"`{datetime.now():%H:%M:%S}` {msg}")

    error, finished = None, False
    run_start = last_event = time.time()
    agent_start_time: dict[int, float] = {}
    
    curr_sim_agent = 0
    events.put(("agent_start", 0))

    while not finished and error is None:
        try:
            while True:
                kind, payload = events.get_nowait()
                last_event = time.time()
                if kind == "agent_start":
                    agent_start_time[payload] = time.time()
                    states[payload] = "working"
                    log(f"{TEAM[payload].ICON} **{TEAM[payload].NAME}** started working")
                elif kind == "tool":
                    idx, tool_name = payload
                    log(f"🔧 {TEAM[idx].NAME} called tool `{tool_name}`")
                elif kind == "agent_done":
                    states[payload] = "done"
                    log(f"✅ **{TEAM[payload].NAME}** finished")
                elif kind == "finished":
                    st.session_state.report = payload
                    finished = True
                elif kind == "error":
                    error = payload
        except queue.Empty:
            pass

        elapsed_total = time.time() - run_start
        if not finished and curr_sim_agent < 4:
            if elapsed_total > 4 and curr_sim_agent == 0:
                states[0] = "done"
                curr_sim_agent = 1
                states[1] = "working"
                agent_start_time[1] = time.time()
                log(f"⚡ **{TEAM[1].NAME}** analyzing tech stack & architecture...")
            elif elapsed_total > 12 and curr_sim_agent == 1:
                states[1] = "done"
                curr_sim_agent = 2
                states[2] = "working"
                agent_start_time[2] = time.time()
                log(f"📝 **{TEAM[2].NAME}** drafting professional README.md...")
            elif elapsed_total > 22 and curr_sim_agent == 2:
                states[2] = "done"
                curr_sim_agent = 3
                states[3] = "working"
                agent_start_time[3] = time.time()
                log(f"🚀 **{TEAM[3].NAME}** crafting LinkedIn launch post...")

        pipeline_box.markdown(pipeline_html(states), unsafe_allow_html=True)
        if "working" in states:
            i = states.index("working")
            mins, secs = divmod(int(time.time() - run_start), 60)
            step_secs = int(time.time() - agent_start_time.get(i, run_start))
            hint = ""
            if time.time() - last_event > 25:
                hint = (
                    "<br><small>⏳ Waiting on Groq LLM model. Free tier token limits may cause short pauses.</small>"
                )
            now_box.markdown(
                f'<div class="now">{TEAM[i].ICON} <b>{TEAM[i].NAME}</b> is working now... '
                f"({step_secs}s &nbsp;·&nbsp; total {mins}:{secs:02d}){hint}</div>",
                unsafe_allow_html=True,
            )
        feed_box.markdown(
            '<div class="feed">' + "<br>".join(feed[-8:]) + "</div>", unsafe_allow_html=True
        )
        time.sleep(0.4)

    now_box.empty()
    if error:
        st.error(f"Something went wrong: {error}")
    else:
        pipeline_box.markdown(pipeline_html(["done"] * len(TEAM)), unsafe_allow_html=True)
        st.balloons()

# ---------- Result ----------
if st.session_state.report:
    st.divider()
    tab1, tab2, tab3 = st.tabs(["📊 Project Analysis", "📝 README.md", "🚀 LinkedIn Post"])
    
    report_text = st.session_state.report
    
    with tab1:
        st.markdown("### Project Analysis & Architecture")
        st.markdown(report_text)
    with tab2:
        st.markdown("### Professional README.md")
        st.code(report_text, language="markdown")
    with tab3:
        st.markdown("### LinkedIn Launch Post")
        st.text_area("Ready-to-post announcement", report_text, height=250)
        
    st.download_button(
        "⬇️ Download Full Report (.md)",
        st.session_state.report,
        file_name="repo_analysis_bundle.md",
        mime="text/markdown",
        use_container_width=True,
    )
