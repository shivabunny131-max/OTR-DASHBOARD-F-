#!/bin/bash

# EC2 Setup Script - Run this on your AWS EC2 instance
# This script installs all dependencies and starts the OTR Dashboard

set -e

echo "🔧 Setting up EC2 Instance for OTR Dashboard..."

# Update system
echo "📦 Updating system packages..."
sudo yum update -y
sudo yum upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker

# Add ec2-user to docker group
sudo usermod -aG docker ec2-user
newgrp docker

# Install Docker Compose
echo "📝 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone GitHub repository
echo "📥 Cloning GitHub repository..."
cd /home/ec2-user
git clone https://github.com/sivadurgapavan/OTR-DASHBOARD-F-.git
cd OTR-DASHBOARD-F-

# Build Docker image
echo "🏗️  Building Docker image..."
docker build -t otr-dashboard:latest .

# Run Docker container
echo "🚀 Starting Docker container..."
docker run -d \
  --name otr-dashboard \
  -p 8501:8501 \
  --restart always \
  otr-dashboard:latest

echo "✅ Dashboard is running!"
echo ""
echo "📊 Access your dashboard:"
echo "   http://<your-instance-ip>:8501"
echo ""
echo "🔍 View logs:"
echo "   docker logs -f otr-dashboard"
echo ""
echo "🛑 Stop container:"
echo "   docker stop otr-dashboard"
echo ""
echo "🔄 Restart container:"
echo "   docker restart otr-dashboard"

# Optional: Install Nginx for reverse proxy
echo ""
echo "🌐 Installing Nginx (optional for reverse proxy)..."
sudo yum install -y nginx

# Create Nginx configuration
echo "⚙️  Configuring Nginx..."
sudo tee /etc/nginx/conf.d/otr-dashboard.conf > /dev/null << EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
}
EOF

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

echo ""
echo "✨ Setup Complete! Your dashboard is ready to use."
echo "   Access it at: http://<your-instance-ip>"
