import pandas as pd

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from datetime import datetime
from dateutil import relativedelta

from prefect import flow, task
from prefect.task_runners import SequentialTaskRunner
from prefect.deployments import DeploymentSpec
from prefect.orion.schemas.schedules import CronSchedule
from prefect.flow_runners import SubprocessFlowRunner


import pickle

from os import path

from  urllib import request


@task
def read_data(path):
    df = pd.read_parquet(path)
    return df

@task
def prepare_features(df, categorical, train=True):
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    mean_duration = df.duration.mean()
    if train:
        print(f"The mean duration of training is {mean_duration}")
    else:
        print(f"The mean duration of validation is {mean_duration}")
    
    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    return df

@task
def train_model(df, categorical):

    train_dicts = df[categorical].to_dict(orient='records')
    dv = DictVectorizer()
    X_train = dv.fit_transform(train_dicts) 
    y_train = df.duration.values

    print(f"The shape of X_train is {X_train.shape}")
    print(f"The DictVectorizer has {len(dv.feature_names_)} features")

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_train)
    mse = mean_squared_error(y_train, y_pred, squared=False)
    print(f"The MSE of training is: {mse}")
    return lr, dv

@task
def run_model(df, categorical, dv, lr):
    val_dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(val_dicts) 
    y_pred = lr.predict(X_val)
    y_val = df.duration.values

    mse = mean_squared_error(y_val, y_pred, squared=False)
    print(f"The MSE of validation is: {mse}")
    return

@task
def get_paths(date=None):

    if date == None:
        date = datetime.now()
    elif type(date) == datetime:
        date = date
    else:
        date = datetime.strptime(date, '%Y-%m-%d')

    train_date = date - relativedelta.relativedelta(months=2)
    val_date = date - relativedelta.relativedelta(months=1)
    
    train_filename = f'fhv_tripdata_{train_date.year}-{train_date.month:02d}.parquet'
    val_filename = f'fhv_tripdata_{val_date.year}-{val_date.month:02d}.parquet'
    
    train_path = f'./data/{train_filename}'
    val_path = f'./data/{val_filename}'
    
    if not path.exists(train_path):
        request.urlretrieve(f'https://nyc-tlc.s3.amazonaws.com/trip+data/{train_filename}', train_path)
    if not path.exists(val_path):
        request.urlretrieve(f'https://nyc-tlc.s3.amazonaws.com/trip+data/{val_filename}', val_path)
    
    return train_path, val_path

@flow(task_runner=SequentialTaskRunner())
def main(date=None):
    
    train_path, val_path = get_paths(date).result()

    categorical = ['PUlocationID', 'DOlocationID']

    df_train = read_data(train_path)
    df_train_processed = prepare_features(df_train, categorical)

    df_val = read_data(val_path)
    df_val_processed = prepare_features(df_val, categorical, False)

    # train the model
    lr, dv = train_model(df_train_processed, categorical).result()
    run_model(df_val_processed, categorical, dv, lr)

    model_save =  open(f'./models/model-{date}.bin', "wb")
    pickle.dump(lr, model_save)
    dv_save = open(f'./models/dv-{date}.bin', "wb")
    pickle.dump(dv, dv_save)


DeploymentSpec(
    flow=main,
    parameters={'date':'2021-08-15'},
    name="deployed-model",
    schedule=CronSchedule(
        cron='0 9 15 * *'),
    flow_runner=SubprocessFlowRunner(),
    tags=["testing"]
)