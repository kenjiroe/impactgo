# static site — build ก่อนด้วย ./run.sh
FROM nginx:alpine
COPY site/ /usr/share/nginx/html/
EXPOSE 80
