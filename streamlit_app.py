import streamlit as st
import requests
import json
import re
import time  # 新增 time 模块用于心跳时间戳

# ================= 剧组配置文件 =================
DIFY_API_KEY = "app-13FM0MX0k6nThq3Dojt4NdlU" 
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
# ===============================================

st.set_page_config(page_title="AI短剧分镜【5集一键复制版】", page_icon="🎬", layout="wide")

# 注入一点 CSS，让复制框更显眼，防止误选
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

# 🧹 一键清空回调函数
def clear_form():
    st.session_state.user_title = ""
    st.session_state.user_input = ""
    st.session_state.full_content = ""

# ================= UI 布局与标题 =================
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("🎬 剧本分镜SOP生成器【V-Team】 (5集一键复制版)")
    st.info("💡 极限测试中：系统已自动将每 **5集** 打包成一个复制模块。一键点击，五倍效率！")
with col_btn:
    # 顶部对齐的一键清空按钮
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    st.button("🗑️ 一键清空", on_click=clear_form, use_container_width=True)

# 绑定了 session_state key 的输入框
user_title = st.text_input("剧名 (Title):", key="user_title", placeholder="例如：The Wrong Text")
user_input = st.text_area("粘贴剧本 (建议控制在10-30集):", key="user_input", height=200)

generate_btn = st.button("🚀 开始批量生成并切分")

# 占位符准备
radar_area = st.empty()

if generate_btn:
    if not user_input:
        st.warning("导演，还没输入剧本呢！")
    else:
        # 点击生成时，先清空上一次的结果
        st.session_state.full_content = ""
        radar_area.empty()
        
        with st.status("🎬 正在实时流式传输分镜内容...", expanded=True) as status:
            heartbeat_box = st.empty() # 节点雷达占位
            progress_box = st.empty()  # 字数进度占位
            
            headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "inputs": {"title": user_title, "raw_script": user_input},
                "response_mode": "streaming",
                "user": "Vanessa-Studio"
            }
            
            try:
                # 强制设定双重超时保护
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 14400))
                response.raise_for_status()
                
                workflow_finished_normally = False
                temp_content = ""
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                event_type = json_data.get('event')
                                
                                # 📡 节点雷达：播报 Dify 底层运行状态
                                if event_type == 'node_started':
                                    node_title = json_data.get('data', {}).get('title', '未知节点')
                                    heartbeat_box.info(f"⚙️ Dify 引擎运转中: 【{node_title}】... [时间: {time.strftime('%H:%M:%S')}]")
                                    
                                # 💓 心跳防静默断网
                                elif event_type == 'ping':
                                    heartbeat_box.caption(f"💓 后台疯狂撰写中... [最近心跳: {time.strftime('%H:%M:%S')}]")
                                    
                                # 📝 文本块接收
                                elif event_type == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    temp_content += chunk
                                    progress_box.text(f"🚀 已接收分镜字符: {len(temp_content)} ...")
                                    
                                # ❌ 捕获报错
                                elif event_type == 'error':
                                    error_msg = json_data.get('message', '未知错误')
                                    st.error(f"❌ Dify 后台发生错误: {error_msg}")
                                    workflow_finished_normally = True
                                    break
                                    
                                # ✅ 完美结束
                                elif event_type == 'workflow_finished':
                                    heartbeat_box.empty()
                                    status.update(label="✅ 全部生成完毕！已进入5集打包阶段。", state="complete", expanded=False)
                                    st.session_state.full_content = temp_content
                                    workflow_finished_normally = True
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                                
                # 防断线报警器
                if not workflow_finished_normally:
                    st.error("⚠️ 警告：超长待机导致连接被异常切断！")
                    st.info("👉 Dify 后台可能仍在继续生成。请稍后前往 Dify 工作流日志提取结果。")
                    if temp_content:
                        st.session_state.full_content = temp_content
                        
            except Exception as e:
                st.error(f"连接失败: {e}")

# ===============================================
# 📦 固化渲染区：只要有结果，就不会因为乱点而消失
# ===============================================
if st.session_state.full_content:
    with radar_area.container():
        st.divider()
        st.subheader("📦 “5集连包”一键复制工作台")
        
        # 1. 先把所有集数切成单片
        raw_episodes = re.split(r'(?=\n#{1,3}\s?EP\s?\d+)|(?=\nEP\s?\d+)|(?=\n第\s?\d+\s?集)', "\n" + st.session_state.full_content)
        
        valid_episodes = []
        for ep in raw_episodes:
            clean_ep = ep.strip()
            if clean_ep and len(clean_ep) > 50: # 过滤掉杂质
                ep_title_search = re.search(r'(EP\s?\d+|第\s?\d+\s?集)', clean_ep)
                ep_name = ep_title_search.group(1) if ep_title_search else "片段"
                valid_episodes.append({"name": ep_name, "content": clean_ep})
        
        # 2. 每 5集 拼装进一个盲盒 
        chunk_size = 5
        for i in range(0, len(valid_episodes), chunk_size):
            chunk = valid_episodes[i:i + chunk_size]
            
            # 动态生成组合标题
            if len(chunk) == 1:
                group_title = chunk[0]['name']
            else:
                group_title = f"{chunk[0]['name']} - {chunk[-1]['name']}"
            
            # 拼接这几集的内容
            group_content = "\n\n---\n\n".join([item['content'] for item in chunk])
            
            # 渲染独立的 UI 容器
            with st.container(border=True):
                st.markdown(f"### 📍 {group_title}")
                with st.expander("👁️ 点击查看分镜预览"):
                    st.markdown(group_content)
                
                st.write(f"👇 点击下方红框右上角的图标，一次性复制 **{len(chunk)}集** 内容：")
                st.code(group_content, language="markdown") 
                st.success(f"已为 {group_title} 准备好复制源")
        
        # 为了防止每次点击按钮都弹气球，可以用一个只触发一次的小魔术
        if getattr(st.session_state, '_show_balloons', True):
            st.balloons()
            st.session_state._show_balloons = False