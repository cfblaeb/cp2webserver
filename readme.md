To deploy: 
- move/copy/link conf/gunicorn.service and socket into /etc/systemd/system/
- move/copy/link conf/ln2_nginx.conf into /etc/nginx/conf.d/
- systemctl enable --now gunicorn.socket
- restart nginx
- test with sudo -u www-data curl --unix-socket /run/gunicorn.sock http
