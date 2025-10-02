import azure.functions as func
import logging
import json
from shared import cosmosdb_client

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="httpget", methods=["GET"])
def http_get(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")

    logging.info(f"Processing GET request. Name: {name}")

    return func.HttpResponse(f"Hello, {name}!")

@app.route(route="mood", methods=["POST"])
def mood_post(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Log the raw request body for debugging
        raw_body = req.get_body()
        logging.info(f"Raw request body: {raw_body}")
        
        # Check if body is empty
        if not raw_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is empty"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Try to parse JSON
        req_body = req.get_json()
        if req_body is None:
            return func.HttpResponse(
                json.dumps({"error": "Request body is not valid JSON"}),
                mimetype="application/json",
                status_code=400
            )
        
        logging.info(f"Parsed JSON body: {req_body}")
        
        text = req_body.get('text')
        user_id = req_body.get('userid')

        # Validate required fields
        if not text or not isinstance(text, str):
            return func.HttpResponse(
                json.dumps({"error": "Missing or invalid 'text' field"}),
                mimetype="application/json",
                status_code=400
            )
        
        if not user_id or not isinstance(user_id, str):
            return func.HttpResponse(
                json.dumps({"error": "Missing or invalid 'userid' field"}),
                mimetype="application/json",
                status_code=400
            )

        mood_db = cosmosdb_client.MoodDatabase()
        mood_id = mood_db.create_mood_entry(
            user_id=user_id,
            text=text,
            analysis=None
        )

        logging.info(f"Processing POST request. Text: {text}, User ID: {user_id}, Mood ID: {mood_id}")

        return func.HttpResponse(
            json.dumps({"mood_id": mood_id}),
            mimetype="application/json"
        )
        
    except ValueError as e:
        logging.error(f"ValueError: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Invalid JSON in request body: {str(e)}"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
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