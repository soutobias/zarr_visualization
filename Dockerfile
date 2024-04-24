FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/

COPY . /code/

COPY pyproject.toml poetry.lock ./
RUN pip install poetry

RUN pip install voila

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-ansi

EXPOSE 8866
CMD ["voila", "notebooks/zarr-visualization.ipynb", "--port=8866", "--no-browser", "--Voila.tornado_settings={'allow_origin': '*'}"]
#     # command: bash -c "voila --port=8866 --no-browser notebooks/zarr-visualization.ipynb"
# voila ComputeEntropy_sub.ipynb --port=8869  --no-browser --Voila.tornado_settings="{'allow_origin': '*'}" &
