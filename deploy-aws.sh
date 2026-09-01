#!/bin/bash

# AWS Deployment Script for OTR Dashboard
# This script automates the deployment of the Nestlé OTR Dashboard to AWS EC2

set -e

echo "🚀 Starting OTR Dashboard AWS Deployment..."

# Configuration
INSTANCE_NAME="OTR-Dashboard"
KEY_NAME="otr-dashboard-key"
SECURITY_GROUP="otr-dashboard-sg"
REGION="us-east-1"
INSTANCE_TYPE="t2.micro"

echo "📋 Configuration:"
echo "  Instance Name: $INSTANCE_NAME"
echo "  Region: $REGION"
echo "  Instance Type: $INSTANCE_TYPE"

# Step 1: Create Security Group
echo "🔐 Creating Security Group..."
aws ec2 create-security-group \
  --group-name $SECURITY_GROUP \
  --description "Security group for OTR Dashboard" \
  --region $REGION 2>/dev/null || echo "Security group already exists"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region $REGION 2>/dev/null || echo "Port 80 already authorized"

aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region $REGION 2>/dev/null || echo "Port 443 already authorized"

aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0 \
  --region $REGION 2>/dev/null || echo "Port 8501 already authorized"

aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region $REGION 2>/dev/null || echo "Port 22 already authorized"

echo "✅ Security Group configured!"

echo ""
echo "📌 Next Steps:"
echo "1. Create EC2 Key Pair (if not exists):"
echo "   aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION --query 'KeyMaterial' --output text > $KEY_NAME.pem"
echo "   chmod 400 $KEY_NAME.pem"
echo ""
echo "2. Launch EC2 Instance:"
echo "   aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 --count 1 --instance-type $INSTANCE_TYPE --key-name $KEY_NAME --security-groups $SECURITY_GROUP --region $REGION"
echo ""
echo "3. Once instance is running, SSH into it and run the setup script:"
echo "   ssh -i $KEY_NAME.pem ec2-user@<your-instance-ip>"
echo ""
echo "For more details, see AWS-DEPLOYMENT.md"
