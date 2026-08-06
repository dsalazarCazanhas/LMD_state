FROM n8nio/n8n:1.121.0

USER root
RUN apk add --no-cache python3 py3-pip pipx

USER node
RUN pipx ensurepath
RUN pipx install uv
