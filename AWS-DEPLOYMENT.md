# AWS Deployment Guide - Nestlé OTR Dashboard

Complete step-by-step guide to deploy your dashboard on AWS.

## Prerequisites

- AWS Account (free tier eligible)
- AWS CLI installed locally
- Git installed
- SSH client

## Step 1: Install AWS CLI

```bash
# On Mac (using Homebrew)
brew install awscli

# Or download from: https://aws.amazon.com/cli/
```

## Step 2: Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Default output format: `json`

Get your credentials from: https://console.aws.amazon.com/iam/

## Step 3: Create Key Pair

```bash
# Create a new key pair
aws ec2 create-key-pair \
  --key-name otr-dashboard-key \
  --region us-east-1 \
  --query 'KeyMaterial' \
  --output text > otr-dashboard-key.pem

# Set proper permissions
chmod 400 otr-dashboard-key.pem
```

## Step 4: Run Deployment Setup Script

```bash
# Run the automated setup (creates security groups, etc.)
chmod +x deploy-aws.sh
./deploy-aws.sh
```

## Step 5: Launch EC2 Instance

### Option A: Using AWS Console (Recommended for beginners)

1. Go to https://console.aws.amazon.com/ec2/
2. Click **Launch Instances**
3. Select **Amazon Linux 2 AMI** (free tier eligible)
4. Instance type: **t2.micro** (free tier)
5. Click **Next: Configure Instance Details**
6. Click **Next** through the remaining steps
7. Security Group: Select `otr-dashboard-sg`
8. Key pair: Select `otr-dashboard-key`
9. Click **Launch**

### Option B: Using AWS CLI

```bash
# Find latest Amazon Linux 2 AMI
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text

# Launch instance (replace AMI-ID)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t2.micro \
  --key-name otr-dashboard-key \
  --security-groups otr-dashboard-sg \
  --region us-east-1
```

## Step 6: Get Instance IP Address

```bash
# Get public IP
aws ec2 describe-instances \
  --filters "Name=key-name,Values=otr-dashboard-key" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

Or check AWS Console: EC2 → Instances

## Step 7: SSH into Instance

```bash
# Connect to your instance
ssh -i otr-dashboard-key.pem ec2-user@<YOUR-INSTANCE-IP>

# Example:
ssh -i otr-dashboard-key.pem ec2-user@54.123.45.67
```

## Step 8: Run Setup Script on EC2

Once connected to your instance:

```bash
# Clone the repository
git clone https://github.com/sivadurgapavan/OTR-DASHBOARD-F-.git
cd OTR-DASHBOARD-F-

# Make setup script executable
chmod +x setup-ec2.sh

# Run setup script
./setup-ec2.sh
```

This will:
- Install Docker
- Install Docker Compose
- Install Nginx
- Clone your GitHub repo
- Build Docker image
- Start the dashboard

## Step 9: Access Your Dashboard

```
http://<YOUR-INSTANCE-IP>:8501
```

Or if using Nginx:
```
http://<YOUR-INSTANCE-IP>
```

## Step 10: Set Up Custom Domain (Optional)

### Using Route 53

1. Go to https://console.aws.amazon.com/route53/
2. Click **Hosted Zones**
3. Create hosted zone for `nestle-southindia-otr-dashboard.com`
4. Create **A record** pointing to your EC2 instance IP
5. Update instance security group to allow traffic on port 443

### Using Let's Encrypt (Free SSL)

```bash
# SSH into your instance
ssh -i otr-dashboard-key.pem ec2-user@<YOUR-INSTANCE-IP>

# Install Certbot
sudo yum install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d nestle-southindia-otr-dashboard.com
```

## Useful Commands

### View Dashboard Logs
```bash
ssh -i otr-dashboard-key.pem ec2-user@<YOUR-INSTANCE-IP>
docker logs -f otr-dashboard
```

### Stop Dashboard
```bash
ssh -i otr-dashboard-key.pem ec2-user@<YOUR-INSTANCE-IP>
docker stop otr-dashboard
```

### Restart Dashboard
```bash
ssh -i otr-dashboard-key.pem ec2-user@<YOUR-INSTANCE-IP>
docker restart otr-dashboard
```

### Update Code and Redeploy
```bash
ssh -i otr-dashboard-key.pem ec2-user@<YOUR-INSTANCE-IP>
cd OTR-DASHBOARD-F-
git pull origin main
docker build -t otr-dashboard:latest .
docker stop otr-dashboard
docker run -d --name otr-dashboard -p 8501:8501 --restart always otr-dashboard:latest
```

## Cost Estimation

- **t2.micro**: Free tier (if eligible)
- **Data transfer**: First 1GB/month free, then $0.12/GB
- **Elastic IP** (if needed): $0.005/hour when not in use
- **Total monthly cost** (after free tier): ~$5-15/month

## Troubleshooting

### Can't connect to instance
```bash
# Check security group allows SSH (port 22)
aws ec2 describe-security-groups --group-names otr-dashboard-sg

# Add SSH access if needed
aws ec2 authorize-security-group-ingress \
  --group-name otr-dashboard-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0
```

### Dashboard not loading
```bash
# Check Docker is running
docker ps

# Check logs for errors
docker logs otr-dashboard

# Restart Docker service
sudo systemctl restart docker
```

### Port already in use
```bash
# Check what's using port 8501
sudo netstat -tulpn | grep 8501

# Kill the process
sudo kill -9 <PID>
```

## Security Best Practices

1. **Restrict SSH Access**: Don't allow 0.0.0.0/0 for SSH in production
   ```bash
   aws ec2 revoke-security-group-ingress \
     --group-name otr-dashboard-sg \
     --protocol tcp \
     --port 22 \
     --cidr 0.0.0.0/0
   
   aws ec2 authorize-security-group-ingress \
     --group-name otr-dashboard-sg \
     --protocol tcp \
     --port 22 \
     --cidr YOUR-IP/32
   ```

2. **Use Elastic IP** for static IP (optional, charges apply)
   ```bash
   aws ec2 allocate-address --domain vpc
   ```

3. **Enable CloudWatch Monitoring**
   - Go to EC2 Console
   - Enable detailed monitoring
   - Set up alarms for CPU, disk usage

4. **Regular Backups**
   - Create AMI snapshots of your instance
   - Set up automated backups

## Next Steps

- Monitor your dashboard at https://console.aws.amazon.com/ec2/
- Set up auto-scaling (optional)
- Configure CloudFront CDN for faster access (optional)
- Set up automated deployments with GitHub Actions

## Support

For issues:
1. Check [AWS Documentation](https://docs.aws.amazon.com/ec2/)
2. Review logs: `docker logs otr-dashboard`
3. Check AWS Console for instance status

---

**Dashboard Repository**: https://github.com/sivadurgapavan/OTR-DASHBOARD-F-

**Happy Deploying! 🚀**
