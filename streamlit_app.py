import streamlit as st
import requests
import json
import re

# ================= 剧组配置文件 =================
DIFY_API_KEY = "app-13FM0MX0k6nThq3Dojt4NdlU" 
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
# ===============================================

st.set_page_config(page_title="北美短剧分镜【10集极限打包版】", page_icon="🎬", layout="wide")

# 注入一点 CSS，让复制框更显眼，防止误选
st.markdown("""
    <style>
    .stCodeBlock { border: 2px solid #ff4b4b !important; border-radius: 10px; }
    .ep-container { padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 25px; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 分镜生成器 - 极限十拼版 (10集/次)")
st.info("💡 极限测试中：系统已自动将每 **10集** 打包成一个复制模块。一键点击，十倍效率！")

user_title = st.text_input("剧名 (Title):", placeholder="例如：The Wrong Text")
user_input = st.text_area("粘贴剧本 (建议控制在10-30集):", height=200)

if st.button("🚀 开始批量生成并切分"):
    if not user_input:
        st.warning("导演，还没输入剧本呢！")
    else:
        progress_box = st.empty()
        full_content = ""
        
        with st.status("🎬 正在实时流式传输分镜内容...", expanded=True) as status:
            headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "inputs": {"title": user_title, "raw_script": user_input},
                "response_mode": "streaming",
                "user": "Vanessa-Studio"
            }
            
            try:
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True, timeout=(300, 7200))
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_str = decoded_line[5:].strip()
                            try:
                                json_data = json.loads(data_str)
                                if json_data.get('event') == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_content += chunk
                                    progress_box.text(f"🚀 已接收分镜字符: {len(full_content)} ...")
                                elif json_data.get('event') == 'workflow_finished':
                                    status.update(label="✅ 全部生成完毕！已进入10集打包阶段。", state="complete", expanded=False)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                st.error(f"连接失败: {e}")

        # --- 自动切分并进行 10集 打包 ---
        if full_content:
            st.divider()
            st.subheader("📦 “10集连包”一键复制工作台")
            
            # 1. 先把所有集数切成单片
            raw_episodes = re.split(r'(?=\n#{1,3}\s?EP\s?\d+)|(?=\nEP\s?\d+)|(?=\n第\s?\d+\s?集)', "\n" + full_content)
            
            valid_episodes = []
            for ep in raw_episodes:
                clean_ep = ep.strip()
                if clean_ep and len(clean_ep) > 50: # 过滤掉杂质
                    # 提取单集标题
                    ep_title_search = re.search(r'(EP\s?\d+|第\s?\d+\s?集)', clean_ep)
                    ep_name = ep_title_search.group(1) if ep_title_search else "片段"
                    valid_episodes.append({"name": ep_name, "content": clean_ep})
            
            # 2. 每 10集 拼装进一个盲盒 (核心修改点)
            chunk_size = 10
            for i in range(0, len(valid_episodes), chunk_size):
                chunk = valid_episodes[i:i + chunk_size]
                
                # 动态生成组合标题 (例如: EP1 - EP10)
                if len(chunk) == 1:
                    group_title = chunk[0]['name']
                else:
                    group_title = f"{chunk[0]['name']} - {chunk[-1]['name']}"
                
                # 拼接这几集的内容 (中间加分隔符)
                group_content = "\n\n---\n\n".join([item['content'] for item in chunk])
                
                # 渲染独立的 UI 容器
                with st.container(border=True):
                    st.markdown(f"### 📍 {group_title}")
                    
                    with st.expander("👁️ 点击查看分镜预览"):
                        st.markdown(group_content)
                    
                    st.write(f"👇 点击下方红框右上角的图标，一次性复制 **{len(chunk)}集** 内容：")
                    st.code(group_content, language="markdown") 
                    st.success(f"已为 {group_title} 准备好复制源")
            
            st.balloons()