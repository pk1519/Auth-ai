
# AuthAI - Real-Time Behavioral Biometrics Authentication System

🔒 **An Advanced Authentication System with Real-time Behavioral Monitoring**

AuthAI combines behavioral biometrics with traditional authentication to provide a comprehensive security solution. The system monitors user behavior patterns in real-time to detect potential bot activities and unauthorized access attempts.

## 🌟 Features

### Authentication System
- **User Registration & Login**: Secure user account creation and authentication
- **MongoDB Integration**: Robust user data storage with bcrypt password hashing
- **Session Management**: Secure session handling with automatic logout
- **User Profile Management**: Profile viewing and password change functionality

### Behavioral Biometrics Monitoring
- **Real-time Monitoring**: Continuous behavioral pattern analysis
- **Machine Learning Detection**: Multiple ML models for bot detection
- **Interactive Dashboard**: Live visualization of behavioral metrics
- **Bot Simulation**: Built-in bot simulator for testing

### Security Features
- **Password Encryption**: Bcrypt hashing for secure password storage
- **Unique Constraints**: Username and email uniqueness enforcement
- **Session Security**: Automatic session cleanup on logout
- **Authentication Guards**: Protected routes and functionality

## 📁 Project Structure

```
Auth ai/
├── authai_streamlit_app.py    # Main Streamlit application with auth
├── authai_core.py             # Core behavioral monitoring system
├── user_auth.py               # MongoDB user authentication module
├── auth_pages.py              # Authentication UI pages (login/signup)
├── setup_database.py          # Database setup and testing script
├── requirements.txt           # Python dependencies
├── models/                    # ML models directory
│   ├── *.keras               # Neural network models
│   ├── *.joblib              # Scikit-learn models
│   └── model_comparison_results.csv
└── README.md                  # This file
```

## 🚀 Quick Start

### No-Auth Mode (Default in this repo)
- This project is configured to run WITHOUT any login/authentication screens.
- MongoDB is NOT required in no-auth mode.

Steps:
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app
   ```bash
   streamlit run authai_streamlit_app.py
   ```
3. Open the browser and use the dashboard directly (you will see "Guest" as the user).

### Prerequisites

1. **Python 3.8+** installed
2. (Optional) **MongoDB** if you re-enable authentication.
   - For no-auth mode, you can ignore MongoDB entirely.

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Setup Database (only if you plan to re-enable auth)
   ```bash
   python setup_database.py
   ```
   This will test MongoDB and create demo users. Not needed in no-auth mode.

3. **Run the Application**
   ```bash
   streamlit run authai_streamlit_app.py
   ```

### Test Credentials (Auth mode only)

If you re-enable auth and run `setup_database.py`, you can use these test accounts:

| Username  | Password | Role     |
|-----------|----------|---------|
| admin     | admin123 | Admin    |
| testuser  | test123  | User     |
| demo_user | demo123  | Demo     |

## 🎯 How to Use

### 1. First Time Setup (No-Auth Mode)
1. Navigate to `http://localhost:8501`
2. Click "Initialize System" in the sidebar to load models
3. Click "Start Monitor" to begin

### 2. Login Process
No login in no-auth mode.

### 3. Dashboard Features
- **User Info**: Shows "Guest" user
- **Reset**: Clears the current session state
- **AuthAI Monitoring**: Real-time behavioral analysis

### 4. AuthAI Monitoring
1. Click "Initialize System" to load ML models
2. Click "Start Monitor" to begin behavior tracking
3. Use "Run Bot Simulator" to test detection
4. View real-time charts and metrics

## 🛠 Technical Details

### Database Schema

The MongoDB `users` collection contains:

```javascript
{
  "_id": ObjectId,
  "username": String (unique),
  "email": String (unique),
  "password_hash": String (bcrypt),
  "created_at": DateTime,
  "last_login": DateTime,
  "is_active": Boolean
}
```

### Authentication Flow

1. **Registration**: 
   - Validates input fields
   - Checks for existing users
   - Hashes password with bcrypt
   - Stores user in MongoDB

2. **Login**:
   - Verifies credentials
   - Updates last login timestamp
   - Creates session state
   - Redirects to dashboard

3. **Session Management**:
   - Maintains user state in Streamlit
   - Protects authenticated routes
   - Cleans up on logout

### Behavioral Monitoring

The system tracks:
- **Mouse Movement**: Speed and patterns
- **Keyboard Activity**: Typing speed and errors
- **Window Focus**: Application switching behavior
- **Click Patterns**: Mouse click frequency
- **Error Rates**: Backspace/correction usage

## 📊 Machine Learning Models

Supported model types:
- **Random Forest**: Tree-based ensemble method
- **XGBoost**: Gradient boosting framework
- **Neural Networks**: LSTM and Transformer models
- **Isolation Forest**: Anomaly detection
- **Autoencoder**: Deep learning anomaly detection

## 🔧 Configuration

### MongoDB Configuration

Edit `user_auth.py` to modify database settings:

```python
MONGODB_URI = "mongodb://localhost:27017/"  # MongoDB connection
DATABASE_NAME = "authai_db"                # Database name
COLLECTION_NAME = "users"                  # Collection name
```

### Security Settings

- **Password Minimum Length**: 6 characters
- **Session Timeout**: Based on Streamlit session
- **Unique Constraints**: Username and email
- **Password Hashing**: bcrypt with salt

## 🚨 Troubleshooting

### MongoDB Connection Issues

1. **Check MongoDB Service**:
   ```bash
   net start MongoDB  # Windows
   sudo systemctl start mongod  # Linux
   ```

2. **Verify Connection**:
   ```bash
   mongosh
   ```

3. **Check Firewall**: Ensure port 27017 is accessible

### Authentication Issues

- **Clear Browser Cache**: Sometimes sessions persist
- **Check Database**: Verify user exists in MongoDB
- **Password Issues**: Ensure correct password is used
- **Session State**: Restart Streamlit app if needed

### Model Loading Issues

- **Check Models Directory**: Ensure ML models are present
- **Dependencies**: Verify TensorFlow/Scikit-learn installation
- **File Permissions**: Check read permissions on model files

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Future Enhancements

- [ ] Password reset functionality
- [ ] Email verification
- [ ] Role-based access control
- [ ] Multi-factor authentication
- [ ] Advanced behavioral analytics
- [ ] Cloud deployment support
- [ ] API endpoints
- [ ] Mobile app integration

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review MongoDB documentation
- Open an issue on GitHub

---

**AuthAI** - Securing the future with intelligent behavioral authentication 🛡️

# AuthAI Real-Time Monitor

A real-time behavioral biometrics authentication system with interactive GUI built using Streamlit.

## Features

- **Real-time monitoring**: Captures mouse movements, keyboard activity, and window switching behavior
- **Live predictions**: Displays whether the system thinks the user is a Person or Robot
- **Bot simulation**: Built-in bot simulator to test the detection capabilities
- **Interactive dashboard**: Real-time charts and metrics
- **Model flexibility**: Supports multiple ML models (RandomForest, XGBoost, IsolationForest, etc.)

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure you have trained models**:
   - The application expects trained models in the `models/` folder
   - Supported model files: `rf_model.joblib`, `xgb_model.joblib`, `iso_model.joblib`

## Running the Application

1. **Start the Streamlit app**:
   ```bash
   streamlit run authai_streamlit_app.py
   ```

2. **Use the interface**:
   - Click "🚀 Initialize System" in the sidebar to load the trained model
   - Click "▶️ Start Monitor" to begin real-time monitoring
   - Use your computer normally - the system will capture behavioral features
   - Click "🤖 Run Bot Simulator" to simulate bot behavior and see how it gets detected

## GUI Components

### Main Dashboard
- **System Status**: Shows whether monitoring is active
- **Current Prediction**: Real-time Person/Robot classification
- **Confidence Score**: Model prediction confidence
- **Feature Values**: Current behavioral biometric features:
  - Mouse speed (pixels/second)
  - Typing speed (keys/minute)
  - Tab switch rate (/minute)
  - Mouse click rate (/minute)
  - Keyboard error rate (%)
  - Active window duration (seconds)

### Real-Time Charts
- **Prediction Timeline**: Shows predictions and confidence scores over time
- **Feature Charts**: Individual time-series plots for each behavioral feature

### Bot Simulation
- Simulates abnormal behavior patterns that should be flagged as "Robot"
- Runs for 15 seconds with rapid mouse movements, clicking, and typing
- Move mouse to top-left corner to abort simulation early

## How It Works

1. **Feature Capture**: Monitors user interaction patterns in real-time
2. **Feature Computation**: Calculates behavioral metrics over a sliding window (30 seconds)
3. **Model Prediction**: Uses trained ML model to classify behavior as Person or Robot
4. **Real-Time Display**: Updates GUI every 2 seconds with latest predictions
5. **Historical Tracking**: Maintains history of predictions for trend analysis

## Model Information

The application automatically selects the best performing model from available trained models:
- **RandomForest**: Tree-based ensemble method
- **XGBoost**: Gradient boosting classifier  
- **IsolationForest**: Unsupervised anomaly detection
- **Neural Networks**: LSTM/Transformer models (if TensorFlow is available)

## Privacy & Permissions

- The application needs permission to monitor keyboard and mouse events
- No personal data is transmitted - all processing happens locally
- Detection logs are saved to `detections_log.csv` for analysis

## Troubleshooting

- **Permission errors**: Run as administrator on Windows if needed
- **Import errors**: Make sure all dependencies are installed
- **Model not found**: Ensure trained models exist in the `models/` folder
- **Slow performance**: Reduce detection interval or window size in the code

## Files

- `authai_streamlit_app.py`: Main Streamlit GUI application
- `authai_core.py`: Core AuthAI monitoring and simulation classes
- `requirements.txt`: Python dependencies
- `models/`: Directory containing trained ML models
- `detections_log.csv`: Log file of all detections (created automatically)

## Screenshot

<img width="1915" height="863" alt="Screenshot 2025-08-29 003859" src="https://github.com/user-attachments/assets/45911486-e54a-4a96-961e-f24d5b4c9274" />
<img width="1912" height="868" alt="Screenshot 2025-08-29 003917" src="https://github.com/user-attachments/assets/9809cbe0-5046-4002-9e0a-6975c15347ce" />
<img width="1918" height="872" alt="Screenshot 2025-08-29 004023" src="https://github.com/user-attachments/assets/a7df0ed6-c3f1-4ce6-b7c6-ed076d8686e7" />


## contact me-
priyanshu345kumar@gmail.com

Made with ❤️ and some coffee


=======
# AuthAi
>>>>>>> be41e88489690cb18ced8aabf3a2ae4604c89d8d
