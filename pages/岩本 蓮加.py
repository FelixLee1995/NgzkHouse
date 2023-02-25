import streamlit as st
from api import g_msg_api
from message_render import render_msgs

########################################################
#  每个msg页面只有成员名称不一样，  因为streamlit无法动态生成页面#
g_member = '岩本 蓮加'
########################################################

st.title(g_member)
msgs = g_msg_api.get_latest_msgs(g_member)
render_msgs(g_member, msgs)
