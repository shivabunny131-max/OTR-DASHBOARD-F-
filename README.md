# Nestlé India Secondary OTR Dashboard

A comprehensive dashboard for monitoring and analyzing Over-The-Route (OTR) data for Nestlé India's secondary distribution network.

## Features

- **Interactive Dashboard**: Real-time OTR data visualization
- **Advanced Filtering**: Filter by date range, branch, DC code, ASM, brand, and more
- **Root Cause Analysis**: Identify and analyze OTR issues
- **Product Excellence Monitoring**: Track product quality metrics

## Local Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nestle-southindia-otr-dashboard.git
cd nestle-southindia-otr-dashboard
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the dashboard:
```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`

## AWS Deployment

### Option 1: Deploy with Docker on EC2

1. **Create EC2 Instance**:
   - Launch an Ubuntu 20.04+ instance
   - Configure security groups to allow HTTP (80) and HTTPS (443)

2. **Install Docker**:
```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
```

3. **Clone and build**:
```bash
git clone https://github.com/yourusername/nestle-southindia-otr-dashboard.git
cd nestle-southindia-otr-dashboard
docker build -t nestle-otr-dashboard .
docker run -p 80:8501 nestle-otr-dashboard
```

4. **Set up Nginx reverse proxy** (optional for custom domain):
```bash
sudo apt-get install -y nginx
```

Create `/etc/nginx/sites-available/default`:
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name nestle-southindia-otr-dashboard.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart Nginx:
```bash
sudo nginx -s reload
```

### Option 2: Deploy with AWS ECS

1. Push Docker image to ECR
2. Create ECS task definition
3. Create ECS service with load balancer
4. Configure Route53 for custom domain

## Project Structure

```
.
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── data/
│   ├── OTR_Dashboard_Final.csv       # Main data file
│   ├── Product_Master_Normalized.csv # Product master data
│   └── build_manifest.json          # Build manifest
├── qa/                   # Quality assurance files
├── .streamlit/
│   └── config.toml      # Streamlit configuration
└── Dockerfile           # Docker configuration for deployment
```

## Configuration

Edit `.streamlit/config.toml` to customize:
- Server address and port
- Theme colors
- CORS and security settings

## Data Files

- `OTR_Dashboard_Final.csv`: Main OTR transaction data
- `Product_Master_Normalized.csv`: Product reference data
- QA folder contains data quality reports

## Support

For issues or questions, please contact the development team.

## License

Internal use only - Nestlé India
