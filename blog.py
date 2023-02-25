import streamlit as st
from api import g_blog_api
from blog_render import render_blogs

########################################################
#  每个msg页面只有成员名称不一样，  因为streamlit无法动态生成页面#
g_member = '乃木坂博客'
########################################################

st.title(g_member)
blogs = g_blog_api.get_latest_blogs()
render_blogs(blogs)
