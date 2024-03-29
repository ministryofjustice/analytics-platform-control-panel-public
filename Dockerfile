FROM 593291632749.dkr.ecr.eu-west-1.amazonaws.com/node:18.12.1-slim AS jsdep
COPY package.json package-lock.json ./
COPY jest.config.js controlpanel/frontend/static /src/

RUN npm install
RUN mkdir -p dist &&\
  ./node_modules/.bin/babel src/module-loader.js src/components src/javascripts -o dist/app.js -s
RUN ./node_modules/.bin/sass --load-path=node_modules/ --style=compressed src/app.scss:dist/app.css
WORKDIR /src
RUN /node_modules/.bin/jest

FROM 593291632749.dkr.ecr.eu-west-1.amazonaws.com/python:3.9-slim-buster AS base

ARG HELM_VERSION=3.5.4
ARG HELM_TARBALL=helm-v${HELM_VERSION}-linux-amd64.tar.gz
ARG HELM_BASEURL=https://get.helm.sh

ENV DJANGO_SETTINGS_MODULE="controlpanel.settings" \
  HELM_HOME=/tmp/helm \
  HELM_CONFIG_HOME=/tmp/helm/repository \
  HELM_CACHE_HOME=/tmp/helm/cache \
  HELM_DATA_HOME=/tmp/helm/data

# create a user to run as
RUN addgroup -gid 1000 controlpanel && \
  adduser -uid 1000 --gid 1000 controlpanel

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        wget \
        gcc \
        libcurl4-gnutls-dev \
        python3-dev \
        libgnutls28-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/controlpanel

# download and install helm
COPY docker/helm-repositories.yaml /tmp/helm/repository/repositories.yaml
RUN wget ${HELM_BASEURL}/${HELM_TARBALL} -nv -O - | \
  tar xz -C /usr/local/bin --strip 1 linux-amd64/helm && \
  helm repo update && \
  chown -R root:controlpanel ${HELM_HOME} && \
  chmod -R g+rwX ${HELM_HOME}



RUN pip install -U pip

COPY requirements.txt requirements.dev.txt manage.py settings.yaml ./
RUN pip install -U --no-cache-dir pip
RUN pip install -r requirements.txt

# Re-enable dev packages
RUN python3 -m venv --system-site-packages dev-packages \
    && dev-packages/bin/pip3 install -U --no-cache-dir pip \
    && dev-packages/bin/pip3 install -r requirements.dev.txt

USER controlpanel
COPY controlpanel controlpanel
COPY docker docker
COPY tests tests

# install javascript dependencies
COPY --from=jsdep dist/app.css dist/app.js static/
COPY --from=jsdep node_modules/accessible-autocomplete/dist/ static/accessible-autocomplete
COPY --from=jsdep node_modules/govuk-frontend static/govuk-frontend
COPY --from=jsdep node_modules/@ministryofjustice/frontend/moj static/ministryofjustice-frontend
COPY --from=jsdep node_modules/html5shiv/dist static/html5-shiv
COPY --from=jsdep node_modules/jquery/dist static/jquery
COPY --from=jsdep node_modules/jquery-ui/dist/ static/jquery-ui

# empty .env file to prevent warning messages
RUN touch .env

# collect static files for deployment
RUN SLACK_API_TOKEN=dummy python3 manage.py collectstatic --noinput --ignore=*.scss
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "controlpanel.asgi:application"]
