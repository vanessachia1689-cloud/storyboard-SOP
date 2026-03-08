import streamlit as st
import requests
import json
import re

# ================= 剧组配置文件 =================
DIFY_API_KEY = "app-13FM0MX0k6nThq3Dojt4NdlU" 
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
# ===============================================

st.set_page_config(page_title="AI短剧分镜【一键分集复制版】", page_icon="✂️", layout="wide")
st.title("✂️ 分镜生成器 - 极速不断线版")
st.markdown("💡 **操作指南：** 采用流式传输，只要进度条在动就不会断线。生成后每集会自动切分到【一键复制】框。")

user_title = st.text_input("剧名 (Title):", placeholder="例如：The Wrong Text")
user_input = st.text_area("粘贴剧本 (支持多集):", height=200)

if st.button("🚀 开始批量生成并切分"):
    if not user_input:
        st.warning("导演，还没输入剧本呢！")
    else:
        # 创建一个进度占位符
        progress_box = st.empty()
        full_content = ""
        
        with st.status("🎬 引擎点火，正在流式撰写分镜...", expanded=True) as status:
            headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "inputs": {"title": user_title, "raw_script": user_input},
                "response_mode": "streaming", # 强制改回流式，保活连接
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
                                # 捕获文本块并实时显示
                                if json_data.get('event') == 'text_chunk':
                                    chunk = json_data.get('data', {}).get('text', '')
                                    full_content += chunk
                                    progress_box.text(f"已生成字数: {len(full_content)} ...")
                                # 捕获工作流完成信号
                                elif json_data.get('event') == 'workflow_finished':
                                    status.update(label="✅ 全部生成完毕！", state="complete", expanded=False)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                st.error(f"连接失败: {e}")

        # --- 自动切分并显示一键复制框 ---
        if full_content:
            st.divider()
            st.subheader("📦 分集复制区")
            
            # 按照 Episode 或 第X集 进行自动切分
            episodes = re.split(r'(?=###\s?EP\s?\d+)|(?=EP\s?\d+)|(?=第\s?\d+\s?集)', full_content)
            
            for ep in episodes:
                clean_ep = ep.strip()
                if clean_ep:
                    # 尝试抓取标题
                    ep_title_search = re.search(r'(EP\s?\d+|第\s?\d+\s?集)', clean_ep)
                    ep_name = ep_title_search.group(1) if ep_title_search else "内容片段"
                    
                    with st.expander(f"📁 点击展开预览：{ep_name}", expanded=False):
                        st.markdown(clean_ep)
                    
                    # 使用 st.code 实现一键复制
                    st.code(clean_ep, language="markdown")
                    st.caption(f"👆 点击上方黑框右上角图标一键复制 {ep_name}")
            
            st.balloons()