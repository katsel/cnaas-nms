FROM debian:buster
ARG BUILDBRANCH=develop

# Create directories
RUN mkdir -p /opt/cnaas
RUN mkdir /opt/cnaas/templates
RUN mkdir /opt/cnaas/settings
RUN mkdir /etc/cnaas-nms

# Copy configuration files
COPY config/db_config.yml /etc/cnaas-nms/db_config.yml
COPY config/api.yml /etc/cnaas-nms/api.yml
COPY config/repository.yml /etc/cnaas-nms/repository.yml
COPY config/plugins.yml /etc/cnaas-nms/plugins.yml

# Setup script
COPY cnaas-setup.sh /opt/cnaas/cnaas-setup.sh
RUN /opt/cnaas/cnaas-setup.sh $BUILDBRANCH

# Prepare for supervisord, uwsgi, ngninx
COPY nosetests.sh /opt/cnaas/
COPY exec-pre-app.sh /opt/cnaas/
COPY config/uwsgi.ini /opt/cnaas/venv/cnaas-nms/
COPY config/supervisord_app.conf /etc/supervisor/supervisord.conf
COPY config/nginx_app.conf /etc/nginx/sites-available/
COPY config/nginx.conf /etc/nginx/
COPY cert/* /etc/nginx/conf.d/

# Websocket test client
RUN mkdir /opt/cnaas/static
COPY client.html /opt/cnaas/static

# Give nginx some special treatment
RUN unlink /etc/nginx/sites-enabled/default
RUN ln -s /etc/nginx/sites-available/nginx_app.conf /etc/nginx/sites-enabled/default
RUN chown www-data:www-data /var/log/nginx
RUN chown www-data:www-data /etc/cnaas-nms/repository.yml
RUN chown -R  www-data:www-data /var/log/nginx/
RUN chown -R www-data:www-data /var/lib/nginx
RUN chown www-data:www-data /var/lib/nginx/
# Give permission for API to clone/sync repos
RUN chown www-data:www-data /opt/cnaas
RUN chown -R www-data:www-data /opt/cnaas/templates
RUN chown -R www-data:www-data /opt/cnaas/settings
# Give permission for unittests
RUN chown root:www-data /opt/cnaas/nosetests.sh
RUN chmod g+rx /opt/cnaas/nosetests.sh
RUN chown -R www-data:www-data /opt/cnaas/venv/cnaas-nms/src


# Expose HTTPS
EXPOSE 1443

ENTRYPOINT supervisord -c /etc/supervisor/supervisord.conf
