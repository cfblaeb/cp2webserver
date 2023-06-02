To deploy run gunicorn  
``` bash
gunicorn -b 127.0.0.1:8911 app:app
```
and setup forwarding in nginx (and possibly dns server)
``` nginx
server {
    listen 80;
    server_name ln2.dumdata.dk
    
    location / {
        proxy_pass http://127.0.0.1:8911/;
    }
}
```
