FROM quay.io/operator-framework/ansible-operator:v0.10.0

USER 0
RUN echo 'jinja2_extensions = jinja2.ext.do,jinja2.ext.loopcontrols' >> /etc/ansible/ansible.cfg && \
    echo 'stdout_callback = yaml' >> /etc/ansible/ansible.cfg
USER ${USER_UID}

COPY watches.yaml ${HOME}/watches.yaml

COPY roles/ ${HOME}/roles/
