FROM apache/airflow:2.10.5
# FROM apache/airflow:3.0.2
# Switch to root for installing system dependencies
USER root
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean
# Create scripts directory and copy scripts
COPY ./scripts/ /opt/airflow/scripts/
# Strip CRLF in case of a Windows checkout without .gitattributes applied
RUN sed -i 's/\r$//' /opt/airflow/scripts/*.sh && chmod +x /opt/airflow/scripts/*.sh

# Switch back to airflow user for installing Python packages and runtime
USER airflow

# Python packages are installed with uv, which the base image ships. Airflow's own
# environment is the virtualenv at /home/airflow/.local ($VIRTUAL_ENV), so `uv pip
# install` targets it directly.
#
# Install Python dependencies from pyproject.toml (dataflow + [airflow] providers + [dbt]).
# Copy only pyproject.toml and a stub package first so this layer stays cached until
# dependencies change. apache-airflow is pinned to the base image's version
# ($AIRFLOW_VERSION) so the resolver can never up/downgrade Airflow - the base image's
# pins (Airflow's constraints) are the source of truth here, not uv.lock, which locks
# the dataflow package for local development and tests.
# Editable (-e): dataflow/config.py finds configs/, schemas/ and sql/ relative to
# /opt/airflow/dataflow - a site-packages copy would not.
WORKDIR /opt/airflow
COPY --chown=airflow:root pyproject.toml ./
COPY --chown=airflow:root dataflow/__init__.py ./dataflow/__init__.py
RUN uv pip install --no-cache "apache-airflow==${AIRFLOW_VERSION}" -e ".[airflow]"

# dbt gets its own virtualenv: dbt-core 1.7 needs sqlparse<0.5, which would downgrade
# apache-airflow-providers-common-sql below what the mysql/postgres providers require.
# Only the [dbt] list from pyproject.toml is installed (not dataflow and its drivers);
# `dbt` on PATH points into this venv. setuptools provides the distutils shim that
# dbt-core 1.7 imports and Python 3.12 no longer ships.
RUN uv venv /home/airflow/dbt-venv && \
    uv pip install --no-cache --python /home/airflow/dbt-venv/bin/python setuptools $(python -c \
      "import tomllib; print(' '.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['optional-dependencies']['dbt']))")
USER root
RUN ln -s /home/airflow/dbt-venv/bin/dbt /usr/local/bin/dbt
USER airflow

# Now copy the dataflow code (docker-compose also mounts it for local development)
COPY --chown=airflow:root dataflow/ ./dataflow/

# Set entrypoint
ENTRYPOINT ["/opt/airflow/scripts/entrypoint.sh"]