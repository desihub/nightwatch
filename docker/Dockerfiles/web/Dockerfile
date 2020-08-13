FROM nginx:latest

RUN chgrp nginx /var/cache/nginx/
RUN chmod g+w /var/cache/nginx/

RUN sed --regexp-extended --in-place=.bak 's%(^\s+listen\s+)80(;)%\18080\2%' /etc/nginx/conf.d/default.conf
EXPOSE 80

RUN sed --regexp-extended --in-place=.bak 's%^pid\s+/var/run/nginx.pid;%pid /var/tmp/nginx.pid;%' /etc/nginx/nginx.conf
ENTRYPOINT ['/bin/bash']
CMD ['-c' , "envsubst '\${PORT}' < /etc/nginx/conf.d/web.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]