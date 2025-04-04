FROM python:3.12 as base

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

FROM base as production

RUN apt-get update && apt-get install -y git
RUN git clone --branch nii_main https://github.com/RCOSDP/coar-notify-inbox.git $APP_HOME

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt --prefer-binary

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
