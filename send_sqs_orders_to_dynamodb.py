import boto3   # allows us to interact with aws services
import uuid    # allows us to generate a unique id

dynamodb = boto3.resource('dynamodb')  # Connect us to use the DynamoDB service
table = dynamodb.Table("orders")       # points us to the "orders" table in dynamodb

def lambda_handler(event, context):   
    for record in event['Records']:    # SQS can deliver multiple messages at once, so loop through each one
        payload = record["body"]       # Extract the actual order content from the SQS message
        print(f"Processing record: {payload}")   # Save the orders to our DynamoDB table with a unique ID as the primary key
        table.put_item(
            Item={
                'orderID': str(uuid.uuid4()),   # generate a unique order ID for each order
                'order': payload                # the raw order content from SQS
            }
        )