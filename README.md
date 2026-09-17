# Serverless Microservice Backend Solution for an E-Commerce Application on AWS

This repository contains step-by-step instructions to design and deploy a serverless, decoupled microservice backend architecture on AWS. 
The solution transforms a legacy on-premises monolithic order service into an asynchronous, scalable system deployed in the us-east-1 region.


## PROBLEM STATEMENT & BUSINESS REQUIEMENTS

The client's legacy order service ran on-premises across 3 Apache HTTPD web servers connected synchronously to a single MySQL database. 
This monolithic design led to severe single-point-of-failure vulnerabilities, high API latencies, and operational overhead during peak events.

### Key business objectives for the AWS migration:

1) Decouple Monolithic Codebase: Isolate order intake from downstream fulfillment services (Inventory, Payment, Accounting, Notifications).

2) Eliminate Synchronous Bottlenecks: Replace real-time blockages with a storage-first, asynchronous event pattern.

3) Minimize Infrastructure Overhead: Avoid managing underlying servers, containers (ECS/EKS), or database infrastructure.

4) Optimize Operational Costs: Transition to a pay-per-use model to align with variable workload traffic.


## ARCHITECTURAL DECISION RECORD (ADR)

1) Compute (AWS Lambda vs. EC2 / ECS / EKS): AWS Lambda provides an event-driven serverless environment without server management overhead or idle infrastructure costs.

2) Database (DynamoDB vs. Aurora Serverless): DynamoDB delivers single-digit millisecond key-value lookups (by orderID) without complex relational join requirements

3) Decoupling (Amazon SQS vs. Direct Invocation): SQS acts as a buffer layer to absorb sudden traffic spikes, eliminate API timeouts, and guarantee message persistence.

4) Fan-Out Messaging (Amazon SNS vs. EventBridge): SNS supplies a lightweight, cost-effective publish/subscribe model to broadcast new orders to all downstream services in parallel.


### PDF GUIDE: [DESIGN A SERVERLESS MICROSERVICE WEB APPLICATION BACKEND ON AWS.pdf](https://github.com/user-attachments/files/32195467/DESIGNING.A.SERVERLESS.MICROSERVICE.WEB.APPLICATION.BACKEND.ON.AWS.pdf)

### WATCH VIDEO WALKTHROUGH HERE: https://youtu.be/eZIWdjVleBQ


## STEP-BY-STEP IMPLEMENTATION GUIDE

#### Step 1: Prerequisites & IAM Setup

1) Log into your AWS Console using an IAM User with AdministratorAccess (e.g., chinedu_2).

2) Set your working region to us-east-1 (N. Virginia) across all services.


#### Step 2: Create IAM Policies

1) Navigate to IAM -> Policies -> Create Policy -> JSON tab and create the following four policies:

Policy 1: `Lambda-write-to-dynamodb` 
Policy 2: `Lambda-publish-to-SNS`
Policy 3: `Lambda-read-from-dynamodb-streams`
Policy 4: `Lambda-read-from-SQS`


### Step 3: Create Execution IAM Roles

Navigate to **IAM** -> **Roles** -> **Create Role**.

Role 1: **`Lambda-read-from-SQS-write-to-dynamodb`**
        * **Trusted Entity:** AWS Service -> Lambda
        * **Attached Policies:** `Lambda-read-from-SQS`, `Lambda-write-to-dynamodb`
        * *Record ARN for later step*.
        
Role 2: **`lambda-read-from-dynamodbstreams-write-to-SNS`**
        * **Trusted Entity:** AWS Service -> Lambda
        * **Attached Policies:** `Lambda-read-from-dynamodb-streams`, `Lambda-publish-to-SNS`
        * *Record ARN for later step*.
      
Role 3: **`ApiGateway-push-to-SQS-CloudWatchlogs`**
        * **Trusted Entity:** AWS Service -> API Gateway
        * **Attached Policy:** `AmazonAPIGatewayPushToCloudWatchLogs` (AWS Managed)
        * *Record ARN for later step*.


### Step 4: Create the SQS Queue

1) Navigate to **Amazon SQS** -> **Create queue**.
   
2) **Type:** Standard

3) **Name:** `orders_queue`
   
4) **Encryption:** Enabled (`SSE-SQS`)
   
5) **Access Policy:** Select **Basic**:
   * **Senders:** *Only the specified AWS accounts, IAM users and roles* -> Paste `ApiGateway-push-to-SQS-CloudWatchlogs` ARN.
   * **Receivers:** *Only the specified AWS accounts, IAM users and roles* -> Paste `Lambda-read-from-SQS-write-to-dynamodb` ARN.

6) Click **Create Queue** and copy the Queue ARN.


### Step 5: Provision the DynamoDB Table

1) Navigate to **DynamoDB** -> **Tables** -> **Create table**.
   
2) **Table name:** `orders`
 
3) **Partition key:** `orderID` (String)
  
4) Keep default settings and click **Create table**.


### Step 6: Deploy Lambda 1 (SQS to DynamoDB)

1) Navigate to **AWS Lambda** -> **Create function**.

2) **Name:** `read-SQS-and-store-in-dynamodb`
  
3) **Runtime:** Python 3.12+

4) **Execution Role:** Choose existing -> Select `Lambda-read-from-SQS-write-to-dynamodb`.

5) **Add Trigger:** Choose **SQS** -> Select `orders_queue` -> Click **Add**.

6) Insert code into `lambda_function.py` and click **Deploy**:


### Step 7: Enable DynamoDB Streams

1) Open the `orders` table in the **DynamoDB Console**.

2) Navigate to the **Exports and streams** tab.

3) Locate **DynamoDB stream details** -> Click **Turn on**.

4) Select **New image** -> Click **Turn on stream**.


### Step 8: Provision the SNS Fan-Out Topic

1) Navigate to **Amazon SNS** -> **Topics** -> **Create topic**.
  
2) **Type:** Standard | **Name:** `sns_orders_topic`

3) **Access Policy:** Choose **Advanced**. Update `AWS` principal allowed to publish to the ARN of `lambda-read-from-dynamodbstreams-write-to-SNS`.

4) Click **Create Topic** and copy the Topic ARN.

5) **Create Subscription:**
   * **Protocol:** Email
   * **Endpoint:** *Enter your email address*
   * Open the confirmation email sent to your inbox and click **Confirm Subscription**.
  

### Step 9: Deploy Lambda 2 (Streams to SNS)

1) Navigate to **AWS Lambda** -> **Create function**.

2) **Name:** `read-dynamodbstreams-and-write-to-sns-topic`

3) **Runtime:** Python 3.12+

4) **Execution Role:** Choose existing -> Select `lambda-read-from-dynamodbstreams-write-to-SNS`.

5) **Add Trigger:** Select **DynamoDB** -> Choose `orders` table -> Click **Add**.

6) Insert code into `lambda_function.py` (replacing `<ENTER_YOUR_SNS_TOPIC_ARN>`) and click **Deploy**:


### Step 10: Configure & Integrate API Gateway

1) Navigate to **API Gateway** -> **Create API** -> **REST API** (Build).

2) **API Name:** `orders-service-SQS-api`

3) **Create Resource:** Name it `order-requests`.

4) **Create Method:** Select `POST` under `/order-requests`:
   * **Integration Type:** AWS Service
   * **AWS Region:** `us-east-1`
   * **AWS Service:** Simple Queue Service (SQS)
   * **HTTP Method:** POST
   * **Action Type:** Use path override -> `<YOUR_ACCOUNT_ID>/orders_queue`
   * **Execution Role:** Paste `ApiGateway-push-to-SQS-CloudWatchlogs`

5) **Edit Integration Request**:
   * **Request Body Passthrough:** Never
   * **HTTP Headers:** Add Header `Content-Type` with mapped value `'application/x-www-form-urlencoded'`
   * **Mapping Templates:** Add `application/json` mapping template:
     ```vtl
     Action=SendMessage&MessageBody=$input.body
     ```

## END-TO-END VERIFICATION

1) Navigate to the **POST method execution page** in API Gateway and click **Test**.

2) Submit the following test JSON request payload:
   ```json
   {
     "item": "noise canceling headset",
     "customerID": "12345"
   }
   ```
   
3) **Validate HTTP 200 Response:** Confirm that API Gateway returns an HTTP 200 status code with an integration latency under 50ms.

4) **Check DynamoDB Record:** Open the `orders` table in DynamoDB -> Click **Explore Table Items** -> Confirm the item has been written with a auto-generated UUID `orderID`.

5) **Verify SNS Email Notification:** Open your email inbox to confirm receipt of the automated notification containing the order payload parsed from DynamoDB Streams.
```json
{
  "orderID": {"S": "2607c8e0-88a6-4f8e-b041-6bc9b3c87b87"},
  "order": {"S": "{\"item\": \"noise canceling headset\", \"customerID\": \"12345\"}"}
}
```

