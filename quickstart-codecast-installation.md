# CodeCast - Quick Installation Guide

## 🚀 5-Minute Setup

CodeCast is one of the easiest interview platforms to set up. Here's how to get it running quickly:

## Prerequisites
- Node.js (v14 or higher)
- npm or yarn
- Git

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Yadvendra016/CodeCast.git
cd CodeCast
```

### 2. Install Dependencies
```bash
npm install
# or
yarn install
```

### 3. Configure Environment (Optional)
Create a `.env` file if you need custom configuration:
```env
PORT=3000
# Add any other configuration needed
```

### 4. Start the Application
```bash
npm start
# or
yarn start
```

### 5. Access the Platform
Open your browser and navigate to:
```
http://localhost:3000
```

## 🎯 How to Use

### For Interviewers:
1. **Create a Room**
   - Click "Create New Room" or use the generated Room ID
   - Share the Room ID with the candidate
   - Set your username (e.g., "Interviewer - John")

### For Candidates:
1. **Join the Room**
   - Enter the Room ID shared by the interviewer
   - Set your username (e.g., "Candidate - Jane")
   - Click "Join"

### During the Interview:
- **Real-time Collaboration**: All changes are synced instantly
- **Code Highlighting**: Syntax highlighting for multiple languages
- **Multiple Users**: Support for multiple participants in the same room
- **No Account Required**: Start interviewing immediately

## 🐳 Docker Deployment (Alternative)

If you prefer Docker:

### Create a Dockerfile:
```dockerfile
FROM node:14-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### Build and Run:
```bash
docker build -t codecast .
docker run -p 3000:3000 codecast
```

## ☁️ Quick Cloud Deployment

### Deploy to Heroku:
```bash
# Install Heroku CLI first
heroku create your-codecast-app
git push heroku main
heroku open
```

### Deploy to Railway:
1. Connect your GitHub repository at [railway.app](https://railway.app)
2. Click "Deploy Now"
3. Your app will be live in minutes

### Deploy to Render:
1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Select "Web Service"
4. Deploy with automatic builds

## 🔧 Customization Options

### Change Editor Theme:
Modify the CodeMirror configuration in the source code to change themes.

### Add Language Support:
CodeCast uses CodeMirror which supports 100+ languages out of the box.

### Add Features:
- Video calling: Integrate WebRTC or services like Daily.co
- Code execution: Add Judge0 API integration
- User authentication: Add Auth0 or Firebase Auth

## 🚨 Troubleshooting

### Port Already in Use:
```bash
# Change port in .env file
PORT=3001
```

### Dependencies Issues:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Connection Issues:
- Ensure firewall allows connections on port 3000
- Check if WebSocket connections are allowed

## 🔒 Security Tips for Production

1. **Add HTTPS**: Use Let's Encrypt for free SSL certificates
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Room Expiry**: Set automatic room expiration after interviews
4. **Access Control**: Add optional password protection for rooms
5. **Monitoring**: Set up logging and monitoring

## 📝 Sample Interview Flow

1. **Pre-Interview** (2 minutes)
   - Interviewer creates room
   - Shares room ID via email/chat
   - Tests connection

2. **Interview Start** (1 minute)
   - Candidate joins room
   - Both parties confirm audio/video (external tool)
   - Agree on problem to solve

3. **Coding Session** (30-45 minutes)
   - Candidate codes solution
   - Interviewer observes in real-time
   - Discussion and questions

4. **Wrap-up** (5 minutes)
   - Review code together
   - Discuss approach
   - Next steps

## 🎉 You're Ready!

Your interview platform should now be running. The total setup time is typically under 5 minutes for local development.

## 📚 Additional Resources

- [CodeCast GitHub](https://github.com/Yadvendra016/CodeCast)
- [Live Demo](https://codecast-324z.onrender.com)
- [CodeMirror Documentation](https://codemirror.net/)
- [Socket.IO Documentation](https://socket.io/docs/)

---

**Pro Tip**: Test the platform with a colleague before your first real interview to ensure everything works smoothly!