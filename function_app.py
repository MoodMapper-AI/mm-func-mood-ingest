import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="httpget", methods=["GET"])
def http_get(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")

    logging.info(f"Processing GET request. Name: {name}")

    return func.HttpResponse(f"Hello, {name}!")

@app.route(route="httppost", methods=["POST"])
def http_post(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        name = req_body.get('name')
        age = req_body.get('age')
        
        logging.info(f"Processing POST request. Name: {name}")

        if name and isinstance(name, str) and age and isinstance(age, int):
            return func.HttpResponse(f"Hello, {name}! You are {age} years old!")
        else:
            return func.HttpResponse(
                "Please provide both 'name' and 'age' in the request body.",
                status_code=400
            )
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON in request body",
            status_code=400
        )


@app.route(route="mood_ingest_http_trigger", auth_level=func.AuthLevel.ANONYMOUS)
def mood_ingest_http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )