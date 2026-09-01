#!/bin/bash

# Automated Custom Domain Setup Script
# Run this on your AWS EC2 instance after deploying the dashboard

set -e

DOMAIN="nestle-southindia-otr-dashboard.com"
EMAIL="your-email@nestle.com"  # Change this to your email

echo "🌐 Setting up custom domain: $DOMAIN"

# Step 1: Update system
echo "📦 Updating system..."
sudo yum update -y

# Step 2: Install Certbot
echo "🔒 Installing Certbot for SSL..."
sudo yum install -y certbot python3-certbot-nginx

# Step 3: Configure Nginx with domain
echo "⚙️  Configuring Nginx..."
sudo tee /etc/nginx/conf.d/otr-dashboard.conf > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

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
        proxy_read_timeout 86400;
    }
}
EOF

# Test Nginx
echo "✅ Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

# Step 4: Get SSL Certificate
echo ""
echo "🔐 Getting SSL certificate from Let's Encrypt..."
echo "   This will prompt you to enter your email address"
echo ""

sudo certbot --nginx -d $DOMAIN

echo ""
echo "✨ SSL Certificate installed successfully!"

# Step 5: Enable auto-renewal
echo "🔄 Enabling automatic certificate renewal..."
sudo systemctl enable certbot-renew
sudo systemctl start certbot-renew

echo ""
echo "✅ Custom domain setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Wait 24-48 hours for DNS propagation"
echo "2. Visit: https://$DOMAIN"
echo "3. Register in Google Search Console"
echo ""
echo "🔍 Check DNS propagation:"
echo "   nslookup $DOMAIN"
echo ""
echo "📊 View logs:"
echo "   sudo tail -f /var/log/nginx/access.log"
