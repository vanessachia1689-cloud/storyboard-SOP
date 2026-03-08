import streamlit as st
import requests
import json
import re

# ================= 剧组配置文件 =================
DIFY_API_KEY = "app-13FM0MX0k6nThq3Dojt4NdlU" 
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
# ===============================================

st.set_page_config(page_title="北美短剧分镜【一键分集复制版】", page_icon="🎬", layout="wide")

# 注入一点 CSS，让复制框更显眼，防止误选 (已修复 Bug)
st.markdown("""
    <style>
    .stCodeBlock { border: 2px solid #ff4b4b !important; border-radius: 10px; }
    .ep-container { padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 25px; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 分镜生成器 - 工业级一键分集版")
st.info("💡 操作提示：生成结束后，下方会按集数出现独立的【复制框】。点击框内右上角图标即可，无需鼠标手动选取。")

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
                response = requests.post(DIFY_API_URL, headers=headers, json=payload, stream=True)
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
                                    status.update(label="✅ 全部生成完毕！已进入分装阶段。", state="complete", expanded=False)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                st.error(f"连接失败: {e}")

        # --- 自动切分并显示分集复制盒 ---
        if full_content:
            st.divider()
            st.subheader("📦 分集“一键复制”工作台")
            
            # 使用更强大的正则，兼容各种 EP 标题格式
            episodes = re.split(r'(?=\n#{1,3}\s?EP\s?\d+)|(?=\nEP\s?\d+)|(?=\n第\s?\d+\s?集)', "\n" + full_content)
            
            for index, ep in enumerate(episodes):
                clean_ep = ep.strip()
                if clean_ep and len(clean_ep) > 50: # 过滤掉太短的杂质
                    # 尝试抓取标题
                    ep_title_search = re.search(r'(EP\s?\d+|第\s?\d+\s?集)', clean_ep)
                    ep_name = ep_title_search.group(1) if ep_title_search else f"内容片段 {index}"
                    
                    # 每一集创建一个独立的带边框容器
                    with st.container(border=True):
                        st.markdown(f"### 📍 {ep_name}")
                        
                        # 提供一个预览区域
                        with st.expander("👁️ 点击查看分镜预览"):
                            st.markdown(clean_ep)
                        
                        # 【核心一键复制框】
                        st.write(f"👇 请点击下方红框右上角的【复制】图标 (无需手动选中文字)：")
                        st.code(clean_ep, language="markdown") 
                        st.success(f"已为 {ep_name} 准备好复制源")
            
            st.balloons()