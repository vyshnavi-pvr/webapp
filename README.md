# webapp


AMI gets created on GitHub Actions and available in dev and demo accounts on AWS using packer.


## Command to Upload Certificates
aws iam upload-server-certificate --server-certificate-name demo_vyshnavi2024_me --certificate-body file://demo_vyshnavi2024_me.crt --private-key file://demo_vyshnavi2024_me.key --certificate-chain file://demo_vyshnavi2024_me.ca-bundle
