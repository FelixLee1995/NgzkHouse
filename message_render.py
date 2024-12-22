import streamlit as st
from dateutil.parser import *
from dateutil import tz
from binary_downloader import g_downloader
import uuid


def render_msgs(member, msgs):
    if msgs is not None:
        for message in msgs:
            pub_time = parse(message['updated_at'])
            to_zone = tz.gettz('Asia/Shanghai')
            local_timestr = pub_time.astimezone(to_zone).strftime('%Y-%m-%d_%H:%M:%S')
            desc = local_timestr + "_" + member
            if message['type'] == 'picture':
                with st.container():
                    if 'text' in message:
                        st.write(message['text'])
                    if 'file' in message:
                        st.image(message['file'])
                    st.caption('发布于 ' + local_timestr)
            if message['type'] == 'text':
                with st.container():
                    if 'text' in message:
                        st.write(message['text'])
                        st.caption('发布于 ' + local_timestr)
            if message['type'] == 'voice':
                with st.container():
                    if 'text' in message:
                        st.write(message['text'])
                    st.audio(message['file'])
                    st.caption('发布于 ' + local_timestr)
                    download_content_bin = g_downloader.download_resource(message['file'])
                    st.download_button(label="Download as m4a", data=download_content_bin, file_name=desc + '.m4a',
                                       mime='application/octet-stream', key=uuid.uuid4().int)
            if message['type'] == 'video':
                with st.container():
                    if 'text' in message:
                        st.write(message['text'])
                    st.video(message['file'])
                    st.caption('发布于 ' + local_timestr)
                    # download_content_bin = g_downloader.download_resource(message['file'])
                    # st.download_button(label="Download as mp4", data=download_content_bin, file_name=desc + '.mp4',
                    #     mime='application/octet-stream', key=uuid.uuid4().int)
