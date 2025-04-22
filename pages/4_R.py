import streamlit as st

# 创建一个带有超链接的按钮
st.markdown(
    """
    <a href="https://yynsd.shinyapps.io/Xiantu/" target="_blank" style="text-decoration: none;">
        <button style="background-color: #007BFF; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
            跳转到 Shiny 应用
        </button>
    </a>
    """,
    unsafe_allow_html=True
)
