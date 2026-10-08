# SpiceDB AWS Fargate cluster
This reference config will create a Fargate cluster exposing gRPC port `50051` over an SSL endpoint.

## The following commands need to run:
1. a network VPC is required for Fargate. Usually, one VPC is enough for multiple services.
   we will reference SubnetA, SubnetB and a VPC ids of our network VPC in the subsequent steps
2. create a cluster using your values for SubnetA, SubnetB and VPC
```
    aws cloudformation create-stack --stack-name permissions-staging --template-body file://./aws/fargate.yaml --parameters ParameterKey=SubnetA,ParameterValue=subnet-0dd.........d9 ParameterKey=SubnetB,ParameterValue=subnet-062........a5 ParameterKey=VPC,ParameterValue=vpc-09a........57 --capabilities CAPABILITY_NAMED_IAM
```

TODO:
1. Parametrize: AWSAccountId, CertificateId, HostedZoneName, ServiceName, etc.
2. Create ECR repository along with the rest of the stack resources
3. Route traffic on ports 8080 and 9090 for SpiceDB dashboard and metrics
