import streamlit as st
from api import g_s46_blog_api
from blog_render import render_s46_blogs

########################################################
#  每个msg页面只有成员名称不一样，  因为streamlit无法动态生成页面#
g_member = '櫻坂博客'
########################################################

st.title(g_member)

blogs = g_s46_blog_api.get_latest_blogs()
render_s46_blogs(blogs)
