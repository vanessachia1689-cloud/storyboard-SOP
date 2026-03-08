import streamlit as st
import requests
import json
import re

# ================= 剧组配置文件 =================
DIFY_API_KEY = "app-qPoN84eZD62hGpaxetu2KTnN"
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
# ===============================================

st.set_page_config(page_title="北美短剧分镜【一键分集复制版】", page_icon="✂️", layout="wide")
st.title("✂️ 分镜生成器 - 飞书/Google专用版")
st.markdown("💡 **操作指南：** 一次性输入多集剧本，生成后每集会有独立的【一键复制】按钮，点击后去飞书粘贴即可。")

user_title = st.text_input("剧名 (Title):", placeholder="My Zombie Bodyguard")
user_input = st.text_area("粘贴剧本 (建议控制在10-30集):", height=200)

if st.button("🚀 开始批量生成并切分"):
    if not user_input:
        st.warning("导演，还没输入剧本呢！")
    else:
        with st.spinner("正在全力生成中，请勿刷新页面..."):
            headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "inputs": {"title": user_title, "raw_script": user_input},
                "response_mode": "blocking", # 这里用阻塞模式，方便最后统一做切分处理
                "user": "Vanessa-Studio"
            }
            
            try:
                response = requests.post(DIFY_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                # 这里的 final_script 需对应你 Dify 输出节点的变量名
                full_content = res_data.get('data', {}).get('outputs', {}).get('final_script', '')
                
                if full_content:
                    # 【核心黑科技】：按照 Episode 或 第X集 进行自动切分
                    # 这里假设 Dify 输出包含 "Episode 1", "Episode 2" 等字样
                    episodes = re.split(r'(?=Episode\s?\d+)|(?=第\s?\d+\s?集)', full_content)
                    
                    for ep in episodes:
                        if ep.strip():
                            # 提取一下这一集的标题，方便实习生看
                            ep_title_search = re.search(r'(Episode\s?\d+|第\s?\d+\s?集)', ep)
                            ep_name = ep_title_search.group(1) if ep_title_search else "内容片段"
                            
                            with st.expander(f"✅ 点击展开：{ep_name}", expanded=True):
                                # 渲染表格给实习生预览
                                st.markdown(ep)
                                # 专门为这一集准备的复制按钮
                                st.code(ep, language="markdown") # st.code 自带一键复制按钮
                                st.caption("点击代码框右上角的图标即可【一键复制本集】")
                    
                    st.balloons()
                else:
                    st.error("Dify 没有返回有效内容，请检查输出节点设置。")
            except Exception as e:
                st.error(f"出错啦: {e}")