prompt_template1 = """Human: I am a AWS solution architect. I need to understand the possible threats for the AWS services involved in an architecture diagram and explain it as a threat model for customers. I Should give a list of every possible threats and its mitigation plans for all the AWS services in the architecture diagram definition in a descriptive manner. Do not use conditional terms like “probably”, “maybe”, “likely” and similar, as this does not build trust. If you are unsure about something, don’t mention it. Be straight to the point, do not start your response by words like “Sure, here is a...".
Use the addional context provided and give the best response relevant to the topic. 
Provide AWS Security best practices for every aws service part of aws architecture diagram. 

Provide the response in a structured manner with contents categorized with below titles:
Overview of diagram
AWS Service Details part of architecture diagram
AWS Security best practices for every aws service part of aws architecture diagram


Context: {context}

Question: {question}

Assistant:"""

prompt_template2 = """Human: This is the second call, 

you have already provided the response in a structured manner with contents categorized for the below titles in the previous call 
Overview of diagram
AWS Service Details part of architecture diagram
AWS Security best practices for every aws service part of aws architecture diagram

Here, I am a AWS solution architect. I need to understand the possible threats for the AWS services involved in an architecture diagram and explain it as a threat model for customers. I Should give a list of every possible threats and its mitigation plans for all the AWS services in the architecture diagram definition in a descriptive manner. Do not use conditional terms like “probably”, “maybe”, “likely” and similar, as this does not build trust. If you are unsure about something, don’t mention it. Be straight to the point, do not start your response by words like “Sure, here is a...".
Use the addional context provided and give the best response relevant to the topic. 

Provide the response in a structured manner with contents categorized with below titles

Threat and Mitigation List based on STRIDE method for every aws service part of aws architecture diagram (Give all possible threats and mitigations. Provide both threats and corresponding mitigation steps.)
List of resources as link which can be followed to find out information more on this

Context: {context}

Question: {question}

Assistant:"""

prompt_template3 = """Human: This is the third call, 

you have already provided the response in a structured manner with contents categorized for the below titles in the previous calls 
Overview of diagram
AWS Service Details part of architecture diagram
AWS Security best practices for every aws service part of aws architecture diagram
Threat and Mitigation List based on STRIDE method for every aws service part of aws architecture diagram (Give all possible threats and mitigations. Provide both threats and corresponding mitigation steps.)
List of resources as link which can be followed to find out information more on this

Here, I am a AWS solution architect. I need to understand the possible threats for the AWS services involved in an architecture diagram and explain it as a threat model for customers. I Should give a list of every possible threats and its mitigation plans for all the AWS services in the architecture diagram definition in a descriptive manner. Do not use conditional terms like “probably”, “maybe”, “likely” and similar, as this does not build trust. If you are unsure about something, don’t mention it. Be straight to the point, do not start your response by words like “Sure, here is a...".
Use the addional context provided and give the best response relevant to the topic. 

Provide Security Recommendations based on aws architecture data flow. Explain data flow between each services in the input architecture in detail in security point of view in below format, don't use the below content or format as is:
Data Encryption at rest and in transit should happen throughout data flow.
    Step-1 : How user is authenticating to S3 bucket to upload data? — User should authenticate to S3 bucket via IAM role authentication or any web UI authentication method if S3 bucket is serving as static website. S3 bucket should not be public if it is not serving static web contents and S3 bucket policy should be restricted and allowed only with specific actions and sources what is needed. S3 bucket should be restricted to accept HTTPS request only.
    Step-2 : EventBridge should have specific S3 bucket event configured as source, it should not allow to receive events from any S3 bucket. S3 bucket should be restricted to accept HTTPS request only.
    Step-3: SQS queue should be encrypted using customer KMS key and SQS access policy should follow least privilege model. SQS policy should allow to send message from specific source. SQS redrive allow policy should allow specific resource to use sqs queue as dead letter queue.
    Step-4: Lambda should be part of VPC as per security best practices and it should make use of VPC endpoints to reach aws public domain service like SQS, SNS, Textract, A2I, S3 & dynamoDB which are part of architecture diagram.

Provide the response in a structured manner with contents categorized with below titles

Security Recommendations based on aws architecture data flow

Context: {context}

Question: {question}

Assistant:"""

prompt_templates = [prompt_template1, prompt_template2, prompt_template3]
