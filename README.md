# limit_exceedance

## Example use:
docker run --rm -it -e OBJECT_PREFIX=example_data --name limit sdswart/limit_exceedance:latest

The model is called from app.py located in /model/app.py as follows:
python app.py

The app will process two files Sample.json and Limit.json and return a list of conditions, such as the following:
[{"Sample": 1, "Condition": "Healthy", "Timestamp": 1602374400.0, "Version": 2.0, "Extra": {"equipment_id": 1234}}]

NOTE: The list may have more than one condition in the returned list based on the number points provided in the Sample.json file. A condition is first created for the earliest data point and further conditions are appended to the list if a change in the urgency is found (e.g. the "condition" changes from "Healthy" to "Low Alarm").
Therefore, if only the latest data point is included in the Sample.json file, only one condition in the returned list is possible.

# Environment variables
The following environment variables are made available:

AWS_ACCESS_KEY_ID - Used to access S3 storage
AWS_SECRET_ACCESS_KEY - Used to access S3 storage
AWS_DEFAULT_REGION - Used to access S3 storage [default = us-east-1]

BUCKET_NAME - Name of S3 bucket
OBJECT_PREFIX - Prefix or folder in which the files (Sample.json and Limit.json) are located

EXTRA_RETURN_ARGS - JSON formatted string which is converted to JSON and added to each returned condition in the key, "Extra". (May be useful for specifying parameters needed to associate the conditions with the correct equipment E.g. EXTRA_RETURN_ARGS={"equipment_id":1234}) [No default]
VERSION - Version of this algorithm which is added to each returned condition [default=2.0]

API_USERNAME - Authentication username for the REST API endpoint to send the result conditions
API_PASSWORD - Authentication password for the REST API endpoint to send the result conditions
API_URL - REST API endpoint URL to send the result conditions
    NOTE: If any of the above three API environment variables are not set, the program will save the result conditions as a file named "Conditions.json" in the same folder as the Sample.json and Limit.json files.

USE_S3 - Boolean ("true" or "false") to specify whether local storage should be used rather than S3 storage for the Sample.json and Limit.json files (Useful for testing) [defualts to "true" if the variable "BUCKET_NAME" is set, otherwise "false"]
DELETE_AFTER_COMPLETION - Boolean ("true" or "false") to specify if the files (Sample.json and Limit.json) should be deleted once the algorithm is complete.
