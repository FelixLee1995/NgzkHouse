docker build  -t idolmsg:1.0 .
docker run --name=idolmsg --restart=always -d -e TZ=Asia/Shanghai -p 7911:8501 -v /home/felixlee/workspace/NgzkLatestMsg/.streamlit:/app/.streamlit  idolmsg:1.0