import streamlit as st
import streamlit.components.v1 as components
from dateutil.parser import *
from dateutil import tz
from binary_downloader import g_downloader
from my_config import g_config



def render_blogs(blogs):
    if blogs is not None:
        for blog in blogs:
            local_timestr = blog['date'].replace('/', '-')
            member = blog['name']

            blog_bg_color = g_config.get_config('blog_bg_color', "#E6E6FA")

            with st.container():
                    st.write(member + ' 发布于 ' + local_timestr)
                    if not blog['img'].startswith('/'):
                        st.image(blog['img'])

                    with st.expander(blog['title']):
                        # blog_expander.markdown()
                        html_title = '<h1>' + blog['title'] + '</h1>'
                        html_content = blog['text']
                        html_content = html_content.replace("/files", "https://www.nogizaka46.com/files")
                        html_str = '<!DOCTYPE html><html><head><meta charset="utf-8"><title></title></head><body style="background-color:#%s">%s%s' \
                                   '</body></html>' % (blog_bg_color, html_title, html_content)
                        st.components.v1.html(html_str, width=None, height=1280, scrolling=True)
