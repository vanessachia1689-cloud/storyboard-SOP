import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import re
import time

# ================= 剧组配置文件 =================
DIFY_API_KEY = "app-13FM0MX0k6nThq3Dojt4NdlU" 
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
# ===============================================

st.set_page_config(page_title="AI短剧分镜【3集一键复制版】", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
    .stCodeBlock { border: 2px solid #ff4b4b !important; border-radius: 10px; }
    .ep-container { padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 25px; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

# --- 记忆芯片初始化 ---
if "user_title" not in st.session_state:
    st.session_state.user_title = ""
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "full_content" not in st.session_state:
    st.session_state.full_content = ""

def clear_form():
    st.session_state.user_title = ""
    st.session_state.user_input = ""
    st.session_state.full_content = ""

# ==========================================
# 🛡️ 核心升级：配置高稳定性强力 Session
# ==========================================
def get_robust_session():
    session = requests.Session()
    # 配置指数退避重试策略 (遇到网络闪断自动重连)
    retry = Retry(
        total=3,             # 总重试次数
        read=3,              # 读取超时重试次数
        connect=3,           # 连接超时重试次数
        backoff_factor=1,    # 重试间隔：1s, 2s, 4s...
        status_forcelist=[500, 502, 503, 504], # 遇到服务器网关错误强制重试
        allowed_methods=["POST"] 
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# ================= UI 布局与标题 =================
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("🎬 剧本分镜SOP生成器【V-Team】 (防断连版)")
    st.info("💡 极速交付：系统已自动将每 **3集** 打包成一个复制模块。已启用底座长连接防断流装甲。")
with col_btn:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    st.button("🗑️ 一键清空", on_click=clear_form, use_container_width=True)

user_title = st.text_input("剧名 (Title):", key="user_title", placeholder="例如：The Wrong Text")
user_input = st.text_area("粘贴剧本 (建议控制在10-30集):", key="user_input", height=200)

generate_btn = st.button("🚀 开始批量生成并切分")

radar_area = st.empty()

if generate_btn:
    if not user_input:
        st.warning("导演，还没输入剧本呢！")
    else:
        st.session_state.full_content = ""
        st.session_state._show_balloons = True 
        radar_area.empty()
        
        with st.status("🎬 正在建立强化通道，实时流式传输分镜内容...", expanded=True) as status:
            heartbeat_box = st.empty() 
            progress_box = st.empty()  
            
            # 🛡️ 核心升级：增加 Connection: keep-alive 强制要求路由节点不要断开
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}", 
                "Content-Type": "application/json",
                "Connection": "keep-alive"
            }
            payload = {
                "inputs": {"title": user_title, "raw_script": user_input},
                "response_mode": "streaming",
                "user": "Vanessa-Studio"
            }
            
            try:
                # 使用我们封装好的强力 Session 发送请求
                http_session = get_robust_session()
                response = http_session.post(
                    DIFY_API_URL, 
                    headers=headers, 
                    json=payload, 
                    stream=True, 
                    timeout=(300, 14400) # (连接超时设置, 读取超时设置)
                )
                response.raise_for_status()
                
                workflow_finished_normally = False
                temp_content = ""
                
                # 🛡️ 核心升级：专门捕获流式解析过程中的网络截断异常
                try:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data:'):
                                data_str = decoded_line[5:].strip()
                                try:
                                    json_data = json.loads(data_str)
                                    event_type = json_data.get('event')
                                    
                                    if event_type == 'node_started':
                                        node_title = json_data.get('data', {}).get('title', '未知节点')
                                        heartbeat_box.info(f"⚙️ Dify 引擎运转中: 【{node_title}】... [时间: {time.strftime('%H:%M:%S')}]")
                                        
                                    elif event_type == 'ping':
                                        heartbeat_box.caption(f"💓 保持连接心跳... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                        
                                    elif event_type == 'text_chunk':
                                        chunk = json_data.get('data', {}).get('text', '')
                                        temp_content += chunk
                                        progress_box.text(f"🚀 已接收分镜字符: {len(temp_content)} ...")
                                        
                                    elif event_type == 'error':
                                        error_msg = json_data.get('message', '未知错误')
                                        st.error(f"❌ Dify 后台发生错误: {error_msg}")
                                        workflow_finished_normally = True
                                        break
                                        
                                    elif event_type == 'workflow_finished':
                                        outputs = json_data.get('data', {}).get('outputs', {})
                                        if 'final_markdown' in outputs:
                                            temp_content = outputs['final_markdown']
                                            
                                        heartbeat_box.empty()
                                        status.update(label="✅ 全部生成完毕！已进入3集打包阶段。", state="complete", expanded=False)
                                        st.session_state.full_content = temp_content
                                        workflow_finished_normally = True
                                        break
                                        
                                except json.JSONDecodeError:
                                    continue
                
                # 捕获最常见的“读取到一半网络崩了”错误
                except requests.exceptions.ChunkedEncodingError:
                    st.error("⚠️ 网络传输中途被物理截断 (流式连接丢失)。")
                    st.info("💡 由于剧本过长，部分中间节点或代理服务器强制断开了连接。系统已保留目前接收到的所有内容。")
                    if temp_content:
                        st.session_state.full_content = temp_content
                                
                if not workflow_finished_normally and not st.session_state.full_content:
                    st.error("⚠️ 警告：连接未正常结束，且未抓取到最终的清洗文本。")
                    if temp_content:
                        st.session_state.full_content = temp_content
                        
            except requests.exceptions.ConnectionError as e:
                st.error(f"🚨 建立连接失败或被拒绝: {e}")
            except requests.exceptions.Timeout as e:
                st.error(f"⏳ 请求超时，请检查网络或 Dify 负载: {e}")
            except Exception as e:
                st.error(f"💥 发生未预期的系统异常: {e}")

# ===============================================
# 📦 固化渲染区：只要有结果，就不会因为乱点而消失
# ===============================================
if st.session_state.full_content:
    with radar_area.container():
        st.divider()
        st.subheader("📦 “3集连包”一键复制工作台")
        
        content_to_split = st.session_state.full_content
        content_to_split = content_to_split.replace("# 🎬 30集完整项目分镜脚本 (极速闪切版)\n\n", "")
        
        if "\n\n---\n\n" in content_to_split:
            raw_episodes = content_to_split.split("\n\n---\n\n")
        else:
            raw_episodes = re.split(r'(?=\n#{1,3}\s?EP\s?\d+)|(?=\nEP\s?\d+)|(?=\n第\s?\d+\s?集)', "\n" + content_to_split)
        
        valid_episodes = []
        for ep in raw_episodes:
            clean_ep = ep.strip()
            if clean_ep and len(clean_ep) > 50:
                ep_title_search = re.search(r'(EP\s?\d+|第\s?\d+\s?集)', clean_ep, re.IGNORECASE)
                ep_name = ep_title_search.group(1).upper() if ep_title_search else "片段"
                valid_episodes.append({"name": ep_name, "content": clean_ep})
        
        chunk_size = 3
        for i in range(0, len(valid_episodes), chunk_size):
            chunk = valid_episodes[i:i + chunk_size]
            
            if len(chunk) == 1:
                group_title = chunk[0]['name']
            else:
                group_title = f"{chunk[0]['name']} - {chunk[-1]['name']}"
            
            group_content = "\n\n---\n\n".join([item['content'] for item in chunk])
            
            with st.container(border=True):
                st.markdown(f"### 📍 {group_title}")
                with st.expander("👁️ 点击查看分镜预览"):
                    st.markdown(group_content)
                
                st.write(f"👇 点击下方红框右上角的图标，一次性复制 **{len(chunk)}集** 内容：")
                st.code(group_content, language="markdown") 
                st.success(f"已为 {group_title} 准备好复制源")
        
        if getattr(st.session_state, '_show_balloons', True):
            st.balloons()
            st.session_state._show_balloons = False