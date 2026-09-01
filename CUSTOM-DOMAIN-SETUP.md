# Custom Domain Setup Guide
# Nestlé India Secondary OTR Dashboard

## 🌐 Domain Setup for nestle-southindia-otr-dashboard.com

This guide walks you through registering and configuring your custom domain.

---

## Step 1: Register Your Domain

### Option A: Using AWS Route 53 (Recommended)

1. Go to: https://console.aws.amazon.com/route53/
2. Click **Registered Domains** → **Register Domain**
3. Search for: `nestle-southindia-otr-dashboard.com`
4. Select the domain and click **Continue**
5. Fill in registrant information
6. Complete payment (~$12/year)
7. Domain will be registered in 1-3 days

### Option B: Using Other Registrars

Popular alternatives:
- **GoDaddy**: https://www.godaddy.com/
- **Namecheap**: https://www.namecheap.com/
- **Google Domains**: https://domains.google/

Cost: ~$10-15/year

---

## Step 2: Get Your AWS EC2 Instance IP Address

Once your EC2 instance is running:

```bash
# Get your Elastic IP or Public IP
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=OTR-Dashboard" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

Or from AWS Console:
1. Go to: https://console.aws.amazon.com/ec2/v2/home#Instances:
2. Find your instance
3. Copy the **Public IPv4 address**

Example: `54.123.45.67`

---

## Step 3: Point Domain to AWS (Using Route 53)

### If you registered with Route 53:

1. Go to **Route 53** → **Hosted Zones**
2. Click your domain name
3. Click **Create Record**
4. Enter these values:
   - **Record name**: `nestle-southindia-otr-dashboard.com`
   - **Type**: `A`
   - **Value**: Your EC2 instance **Elastic IP** (not Public IP)
   - **TTL**: 300

5. Click **Create Records**

### If you registered with another registrar:

1. Log in to your domain registrar
2. Find **DNS Settings** or **Nameservers**
3. Update nameservers to Route 53 nameservers:
   ```
   ns-123.awsdns-45.com
   ns-456.awsdns-78.org
   ns-789.awsdns-90.co.uk
   ns-012.awsdns-34.net
   ```
   
   (Get exact nameservers from Route 53 → Hosted Zones → Your domain)

4. Save changes
5. Wait 24-48 hours for DNS propagation

---

## Step 4: Get an Elastic IP (Recommended)

To ensure your IP doesn't change:

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Get the address
aws ec2 describe-addresses --query 'Addresses[0].PublicIp' --output text

# Associate with instance
aws ec2 associate-address \
  --instance-id i-0123456789abcdef0 \
  --allocation-id eipalloc-0123456789abcdef0
```

Or from AWS Console:
1. Go to **EC2** → **Elastic IPs**
2. Click **Allocate Elastic IP address**
3. Click **Allocate**
4. Select the address
5. Click **Associate Elastic IP address**
6. Select your instance
7. Click **Associate**

**Cost**: ~$0.005/hour if not associated (free if associated)

---

## Step 5: Configure Nginx with Custom Domain

SSH into your EC2 instance:

```bash
ssh -i otr-dashboard-key.pem ec2-user@your-instance-ip
```

Update Nginx configuration:

```bash
sudo tee /etc/nginx/conf.d/otr-dashboard.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name nestle-southindia-otr-dashboard.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
EOF
```

Restart Nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 6: Set Up SSL/HTTPS (Let's Encrypt)

On your EC2 instance:

```bash
# Install Certbot
sudo yum install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d nestle-southindia-otr-dashboard.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect from HTTP to HTTPS
```

Auto-renewal:

```bash
# Enable auto-renewal
sudo systemctl enable certbot-renew
sudo systemctl start certbot-renew
```

---

## Step 7: Test Your Domain

### Wait for DNS Propagation

```bash
# Check DNS propagation
nslookup nestle-southindia-otr-dashboard.com

# Or use online tool:
# https://www.whatsmydns.net/
```

Expected output:
```
Non-authoritative answer:
Name:    nestle-southindia-otr-dashboard.com
Address: 54.123.45.67
```

### Access Your Dashboard

Once DNS is propagated (24-48 hours):

```
https://nestle-southindia-otr-dashboard.com
```

---

## Step 8: Register with Google Search Console

1. Go to: https://search.google.com/search-console
2. Click **+ Create property**
3. Enter: `https://nestle-southindia-otr-dashboard.com`
4. Click **Continue**
5. Verify ownership:
   - Method: **DNS record** (recommended)
   - Copy the TXT record value
   - Add to Route 53
   - Click **Verify**

6. Submit sitemap (optional):
   ```
   https://nestle-southindia-otr-dashboard.com/sitemap.xml
   ```

---

## Troubleshooting

### Domain not resolving

```bash
# Check DNS records
dig nestle-southindia-otr-dashboard.com

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Check firewall rules
aws ec2 describe-security-groups --group-names otr-dashboard-sg
```

### SSL Certificate issues

```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check certificate expiry
sudo certbot certificates
```

### Nginx not working

```bash
# Check Nginx syntax
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# View logs
sudo tail -100 /var/log/nginx/access.log
sudo tail -100 /var/log/nginx/error.log
```

---

## Complete Checklist

- [ ] Domain registered
- [ ] Elastic IP allocated and associated
- [ ] DNS records pointing to Elastic IP
- [ ] Nginx configured with domain
- [ ] SSL certificate installed
- [ ] DNS propagation verified
- [ ] Dashboard accessible at `https://nestle-southindia-otr-dashboard.com`
- [ ] Registered with Google Search Console
- [ ] Sitemap submitted (optional)

---

## Timeline

1. **Domain registration**: 1-3 days
2. **DNS propagation**: 24-48 hours
3. **Total time**: 2-5 days

---

## Costs

| Item | Cost | Note |
|------|------|------|
| Domain (annual) | $12 | Route 53 |
| Elastic IP | Free | If associated |
| EC2 t2.micro | Free* | First 12 months |
| SSL Certificate | Free | Let's Encrypt |
| **Total** | **~$12/year** | *After free tier |

---

## After Setup

Once your domain is live:

1. **Monitor uptime**: Use AWS CloudWatch
2. **Enable backups**: Create EBS snapshots
3. **Update code**: Push to GitHub, redeploy on EC2
4. **Google indexing**: Monitor Search Console
5. **Security**: Enable VPC flow logs, WAF

---

**Need help? Check AWS documentation:**
- Route 53: https://docs.aws.amazon.com/route53/
- Certbot: https://certbot.eff.org/
- Nginx: https://nginx.org/en/docs/

---

Next: After domain is live, your dashboard will be searchable on Google! 🎉
