# Deployment Guide

## Quick Deployment Options

### Option 1: Local Development

1. **Prerequisites**
   - Python 3.9+
   - Node.js 16+
   - Tesseract OCR
   - FFmpeg

2. **Install Tesseract OCR**
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Install FFmpeg**
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # Windows
   # Download from: https://ffmpeg.org/download.html
   ```

4. **Run Setup Script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

5. **Configure API Key**
   Edit `backend/.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

6. **Start Backend**
   ```bash
   cd backend
   source venv/bin/activate  # Windows: venv\Scripts\activate
   uvicorn main:app --reload
   ```

7. **Start Frontend** (new terminal)
   ```bash
   cd frontend
   npm start
   ```

### Option 2: Docker Deployment

1. **Prerequisites**
   - Docker
   - Docker Compose

2. **Configure Environment**
   Create `.env` in project root:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. **Build and Run**
   ```bash
   docker-compose up --build
   ```

4. **Access**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 3: Cloud Deployment (Heroku)

#### Backend on Heroku

1. **Create Heroku App**
   ```bash
   cd backend
   heroku create your-app-name-backend
   ```

2. **Add Buildpacks**
   ```bash
   heroku buildpacks:add --index 1 heroku/python
   heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-apt
   ```

3. **Create Aptfile** (for Tesseract)
   ```
   tesseract-ocr
   tesseract-ocr-eng
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set ANTHROPIC_API_KEY=your-key-here
   ```

5. **Create Procfile**
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

6. **Deploy**
   ```bash
   git push heroku main
   ```

#### Frontend on Vercel/Netlify

1. **Update API URL**
   In `frontend/.env`:
   ```
   REACT_APP_API_URL=https://your-backend.herokuapp.com
   ```

2. **Deploy to Vercel**
   ```bash
   cd frontend
   npm install -g vercel
   vercel
   ```

   Or **Deploy to Netlify**
   ```bash
   npm run build
   netlify deploy --prod --dir=build
   ```

### Option 4: AWS Deployment

#### Backend on AWS EC2

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t2.medium or larger
   - Open ports 22, 80, 8000

2. **SSH into Instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip tesseract-ocr ffmpeg nginx
   ```

4. **Clone and Setup**
   ```bash
   git clone https://github.com/your-repo/ai-interviewer-system.git
   cd ai-interviewer-system/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Run with Supervisor**
   ```bash
   sudo apt install supervisor
   ```

   Create `/etc/supervisor/conf.d/ai-interviewer.conf`:
   ```ini
   [program:ai-interviewer]
   directory=/home/ubuntu/ai-interviewer-system/backend
   command=/home/ubuntu/ai-interviewer-system/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   user=ubuntu
   autostart=true
   autorestart=true
   ```

#### Frontend on AWS S3 + CloudFront

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Create S3 Bucket**
   - Enable static website hosting
   - Upload build files

3. **Configure CloudFront**
   - Create distribution
   - Point to S3 bucket
   - Configure custom domain (optional)

## Environment Variables

### Backend
```env
ANTHROPIC_API_KEY=your_api_key
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
```

### Frontend
```env
REACT_APP_API_URL=http://localhost:8000
```

## Troubleshooting

### Issue: OCR not working
**Solution**: Ensure Tesseract is installed and in PATH
```bash
tesseract --version
```

### Issue: Audio transcription fails
**Solution**: Check FFmpeg installation
```bash
ffmpeg -version
```

### Issue: CORS errors
**Solution**: Update CORS_ORIGINS in backend/config.py

### Issue: API rate limits
**Solution**: Implement request throttling or upgrade Claude API tier

## Performance Optimization

1. **Use Redis for session storage** (instead of in-memory)
2. **Implement CDN** for frontend static files
3. **Add database** for persistent storage (PostgreSQL)
4. **Use worker queues** for long-running tasks (Celery)
5. **Enable caching** for API responses

## Security Considerations

1. **Enable HTTPS** (Let's Encrypt recommended)
2. **Set up authentication** for production
3. **Rate limiting** on API endpoints
4. **Input validation** and sanitization
5. **Regular security updates**

## Monitoring

1. **Application Logs**: Use CloudWatch, Datadog, or Sentry
2. **Performance**: New Relic, Application Insights
3. **Uptime**: Pingdom, UptimeRobot
4. **Error Tracking**: Sentry, Rollbar

## Scaling

1. **Horizontal Scaling**: Use load balancer (AWS ALB, nginx)
2. **Database**: Move to PostgreSQL with connection pooling
3. **Cache Layer**: Redis for sessions and frequently accessed data
4. **Queue System**: RabbitMQ or AWS SQS for async tasks
5. **CDN**: CloudFront or Cloudflare for static assets

---

For more help, check the main README.md or open an issue on GitHub.
