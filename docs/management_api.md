# Management API

MMS provides a set of API allow user to manage models at runtime:
1. [Register a model](#register-a-model)
2. [Increase/decrease number of workers for specific model](#scale-workers)
3. [Describe a model's status](#describe-model)
4. [Unregister a model](#unregister-a-model)
5. [List registered models](#list-models)

Management API is listening on port 8081 and only accessible from localhost by default. To change the default setting, see [MMS Configuration](configuration.md).

Similar as [Inference API](inference_api.md), Management API also provide a [API description](#api-description) to describe management APIs with OpenAPI 3.0 specification.

## Management APIs

### Register a model

`POST /models`
* url - Model archive download url. Supports the following locations:
    * a local model archive (.mar); the file must be directly in model_store folder.
    * a local model directory; the directory must be directly in model_store folder. This option can avoid MMS extracting .mar file to temporary folder, which will improve load time and reduce disk space usage.
    * a URI using the HTTP(s) protocol. MMS can download .mar files from the Internet.
* model_name - the name of the model; this name will be used as {model_name} in other API as path. If this parameter is not present, modelName in MANIFEST.json will be used.
* handler - the inference handler entry-point. This value will override `handler` in MANIFEST.json if present.
* runtime - the runtime for the model custom service code. This value will override runtime in MANIFEST.json if present. The default value is `PYTHON`.
* batch_size - the inference batch size. The default value is `1`.
* max_batch_delay - the maximum delay for batch aggregation. The default value is 100 milliseconds.
* initial_workers - the number of initial workers to create. The default value is `0`. MMS will not run inference until there is at least one work assigned.
* synchronous - whether or not the creation of worker is synchronous. The default value is false. MMS will create new workers without waiting for acknowledgement that the previous worker is online.

```bash
curl -X POST "http://localhost:8081/models?url=https%3A%2F%2Fs3.amazonaws.com%2Fmodel-server%2Fmodels%2Fsqueezenet_v1.1%2Fsqueezenet_v1.1.model"

{
  "status": "Model \"squeezenet_v1.1\" registered"
}
```

User may want to create workers while register, creating initial workers may take some time, user can choose between synchronous or synchronous call to make sure initial workers are created properly.

The asynchronous call will return before trying to create workers with HTTP code 202:

```bash
curl -v -X POST "http://localhost:8081/models?initial_workers=1&synchronous=false&url=https%3A%2F%2Fs3.amazonaws.com%2Fmodel-server%2Fmodels%2Fsqueezenet_v1.1%2Fsqueezenet_v1.1.model"

< HTTP/1.1 202 Accepted
< content-type: application/json
< x-request-id: 29cde8a4-898e-48df-afef-f1a827a3cbc2
< content-length: 33
< connection: keep-alive
< 
{
  "status": "Worker updated"
}
```

The synchronous call will return after all workers has be adjusted with HTTP code 200.

```bash
curl -v -X POST "http://localhost:8081/models?initial_workers=1&synchronous=true&url=https%3A%2F%2Fs3.amazonaws.com%2Fmodel-server%2Fmodels%2Fsqueezenet_v1.1%2Fsqueezenet_v1.1.model"

< HTTP/1.1 200 OK
< content-type: application/json
< x-request-id: c4b2804e-42b1-4d6f-9e8f-1e8901fc2c6c
< content-length: 32
< connection: keep-alive
< 
{
  "status": "Worker scaled"
}
```


### Scale workers

`PUT /models/{model_name}`
* min_worker - (optional) the minimum number of worker processes. MMS will try to maintain this minimum for specified model. The default value is `1`.
* max_worker - (optional) the maximum number of worker processes. MMS will make no more that this number of workers for the specified model. The default is the same as the setting for `min_worker`.
* number_gpu - (optional) the number of GPU worker processes to create. The default value is `0`. If number_gpu exceeds the number of available GPUs, the rest of workers will run on CPU.
* synchronous - whether or not the call is synchronous. The default value is `false`.
* timeout - the specified wait time for a worker to complete all pending requests. If exceeded, the work process will be terminated. Use `0` to terminate the backend worker process immediately. Use `-1` to wait infinitely. The default value is `-1`. 
**Note:** not implemented yet.

Use the Scale Worker API to dynamically adjust the number of workers to better serve different inference request loads.

There are two different flavour of this API, synchronous vs asynchronous.

The asynchronous call will return immediately with HTTP code 202:

```bash
curl -v -X PUT "http://localhost:8081/models/noop?min_worker=3"

< HTTP/1.1 202 Accepted
< content-type: application/json
< x-request-id: 74b65aab-dea8-470c-bb7a-5a186c7ddee6
< content-length: 33
< connection: keep-alive
< 
{
  "status": "Worker updated"
}
```

The synchronous call will return after all workers has be adjusted with HTTP code 200.

```bash
curl -v -X PUT "http://localhost:8081/models/noop?min_worker=3&synchronous=true"

< HTTP/1.1 200 OK
< content-type: application/json
< x-request-id: c4b2804e-42b1-4d6f-9e8f-1e8901fc2c6c
< content-length: 32
< connection: keep-alive
< 
{
  "status": "Worker scaled"
}
```

### Describe model

`GET /models/{model_name}`

Use the Describe Model API to get detail runtime status of a model:

```bash
curl http://localhost:8081/models/noop

{
  "modelName": "noop",
  "modelVersion": "snapshot",
  "modelUrl": "noop.mar",
  "engine": "MXNet",
  "runtime": "python",
  "minWorkers": 1,
  "maxWorkers": 1,
  "batchSize": 1,
  "maxBatchDelay": 100,
  "workers": [
    {
      "id": "9000",
      "startTime": "2018-10-02T13:44:53.034Z",
      "status": "READY",
      "gpu": false,
      "memoryUsage": 89247744
    }
  ]
}
```

### Unregister a model

`DELETE /models/{model_name}`

Use the Unregister Model API to free up system resources:

```bash
curl -X DELETE http://localhost:8081/models/noop

{
  "status": "Model \"noop\" unregistered"
}
```

### List models

`GET /models`
* limit - (optional) the maximum number of items to return. It is passed as a query parameter. The default value is `100`.
* next_page_token - (optional) queries for next page. It is passed as a query parameter. This value is return by a previous API call.

Use the Models API to query current registered models:

```bash
curl "http://localhost:8081/models"
```

This API supports pagination:

```bash
curl "http://localhost:8081/models?limit=2&next_page_token=2"

{
  "nextPageToken": "4",
  "models": [
    {
      "modelName": "noop",
      "modelUrl": "noop-v1.0"
    },
    {
      "modelName": "noop_v0.1",
      "modelUrl": "noop-v0.1"
    }
  ]
}
```


## API Description

`OPTIONS /`

To view a full list of inference and management APIs, you can use following command:

```bash
# To view all inference APIs:
curl -X OPTIONS http://localhost:8080

# To view all management APIs:
curl -X OPTIONS http://localhost:8081
```

The out is OpenAPI 3.0.1 json format. You use it to generate client code, see [swagger codegen](https://swagger.io/swagger-codegen/) for detail.

Example outputs of the Inference and Management APIs:
* [Inference API description output](../frontend/server/src/test/resources/inference_open_api.json)
* [Management API description output](../frontend/server/src/test/resources/management_open_api.json)
