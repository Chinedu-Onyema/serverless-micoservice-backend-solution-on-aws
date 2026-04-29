import boto3
import json

# Connect to SNS using the AWS SDK
client = boto3.client('sns')

def lambda_handler(event, context):

    # DynamoDB Streams can deliver multiple record changes at once, loop through each
    for record in event["Records"]:

        # Only act on new records being inserted — ignore updates and deletes
        if record['eventName'] == 'INSERT':

            # Extract the newly inserted item from the DynamoDB stream record
            new_record = record['dynamodb']['NewImage']

            # Publish the new order as a message to the SNS topic
            response = client.publish(
                TargetArn='<Enter Amazon SNS ARN for your sns-topic>',  # the SNS topic to broadcast to

                # Wrap the record in JSON format — outer layer tells SNS the structure, inner layer is the actual data
                Message=json.dumps({'default': json.dumps(new_record)}),

                # Tells SNS the message is formatted differently per channel (email, SQS, Lambda etc.)
                MessageStructure='json'
            )






