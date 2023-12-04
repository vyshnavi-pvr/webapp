# Webapp


AMI of the web application gets created on GitHub Actions and available in dev and demo accounts on AWS using packer. This AMI will be used as part of Infrastructure as a Code (iac-pulumi) repository.

- Server Operating System : us-east-1: Debian 12 (20230711-1438) ami-06db4d78cb1d3bbf9
- Programming Language: Python
- Relational Database: PostgreSQL
- Object Storage: GCS Cloud Storage Bucket
- NoSQL: Amazon DynamoDB Setting Up DynamoDB Local for development
- Backend Framework: Fast-API
- ORM Framework: SQLAlchemy
- UI Framework: None
- CSS: None

**Command to Upload  SSL certificate from Namecheap** 
```
aws iam upload-server-certificate --server-certificate-name demo_vyshnavi2024_me --certificate-body file://demo_vyshnavi2024_me.crt --private-key file://demo_vyshnavi2024_me.key --certificate-chain file://demo_vyshnavi2024_me.ca-bundle
```
