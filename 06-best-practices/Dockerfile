FROM public.ecr.aws/lambda/python:3.9

RUN pip install -U pip
RUN pip install pipenv

COPY [ "Pipfile", "Pipfile.lock", "./" ]

RUN pipenv install --system --deploy

ADD mlruns ./mlruns

COPY [ "lambda_function.py", "model.py", "mlflow.db", "./" ]

CMD [ "lambda_function.lambda_handler" ]
