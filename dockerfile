FROM python:3.10
RUN mkdir -p /app/pages
RUN mkdir -p /app/.streamlit
# RUN mkdir -p /app/accounts
# RUN mkdir -p /app/src/plugins
# RUN mkdir -p /app/third
ADD ./*.py /app/
ADD ./pages/* /app/pages/
ADD ./requirements.txt /app/
WORKDIR /app/
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
CMD [ "python3", "-m" , "streamlit", "run",  "./blog.py" ]
