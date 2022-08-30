export KINESIS_STREAM_INPUT="my-prod-ride-events-mlops-zoomcamp"
export KINESIS_STREAM_OUTPUT="my-prod-ride-predictions-mlops-zoomcamp"

SHARD_ID=`aws kinesis put-record  \
        --stream-name ${KINESIS_STREAM_INPUT}   \
        --partition-key 1  --cli-binary-format raw-in-base64-out  \
        --data '{"ride": {
            "PULocationID": 130,
            "DOLocationID": 205,
            "trip_distance": 3.66
        },
        "ride_id": 156}'  \
        --query 'ShardId'
    `
SHARD_ID="${SHARD_ID%\"}"
SHARD_ID="${SHARD_ID#\"}"

SHARD_ITERATOR=$(aws kinesis get-shard-iterator --shard-id ${SHARD_ID} --shard-iterator-type TRIM_HORIZON --stream-name ${KINESIS_STREAM_OUTPUT} --query 'ShardIterator')

SHARD_ITERATOR="${SHARD_ITERATOR%\"}"
SHARD_ITERATOR="${SHARD_ITERATOR#\"}"
aws kinesis get-records --shard-iterator $SHARD_ITERATOR
