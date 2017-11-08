Webcan 
======

Getting Started
---------------

## Requirements

* [pyenv](https://github.com/pyenv/pyenv) with python 3.6.2 installed
* A mongodb server

## Installing

```bash
git clone https://github.com/JonnoFTW/webcan
cd webcan
pyenv local 3.6.2
python setup.py develop
```

# Running


After you've setup the application, you'll need to create the collections and databases required:

```bash

```

Now you can run the application with the following:

```bash
export LDAP_SERVER='url.to.ldap'
export LDAP_USERNAME_SUFFIX='suffix.for.ldap.username'
export WEBCAN_MONGO_URI='mongodb://username:password@path.to.server:27017/webcan'
pserve production.ini http_port=80
```

It's highly recommend to use an nginx in front of this server with gzip turned on, include the following in your nginx configuration:

```nginx
upstream webcan {
       server localhost:5000;
}
server {
    listen 6867;
    listen 6868 ssl http2;
    
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    gzip  on;

    gzip_disable "msie6";

    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript application/zip;

    location / {
        proxy_set_header        Host $http_host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        client_max_body_size    10m;
        client_body_buffer_size 128k;
        proxy_connect_timeout   60s;
        proxy_send_timeout      90s;
        proxy_read_timeout      90s;
        proxy_buffering         off;
        proxy_temp_file_write_size 64k;
        proxy_pass http://webcan;
                
    }
    location /static {
        root                    /path/to/webcan/webcan/;
        expires                 30d;
        add_header              Cache-Control public;
        access_log              off;
    }
    location = /favicon.ico {
        alias /path/to/webcan/webcan/static/favicon.ico;
    }
}

```