# AuthAI - Real-Time Behavioral Biometrics Detection System

🔒 **An Advanced Behavioral Monitoring System with Real-time Bot Detection**

AuthAI is a behavioral biometrics system that monitors user behavior patterns in real-time to detect potential bot activities and automated behavior. The system uses machine learning models to classify user interactions as human or bot behavior.

## 🌟 Features

### Real-time Behavioral Monitoring
- **Live Monitoring**: Continuous behavioral pattern analysis
- **Machine Learning Detection**: Multiple ML models for bot detection
- **Interactive Dashboard**: Live visualization of behavioral metrics
- **Bot Simulation**: Built-in bot simulator for testing

### Security Features
- **Real-time Alerts**: Immediate bot detection notifications
- **Confidence Scoring**: Model prediction confidence levels
- **Historical Tracking**: Trend analysis and detection history
- **Multiple Models**: Support for various ML algorithms

## 📁 Project Structure

```
Auth ai/
├── authai_streamlit_app.py    # Main Streamlit application
├── authai_core.py             # Core behavioral monitoring system
├── authai_core_cloud.py       # Cloud-compatible version
├── requirements.txt           # Python dependencies
├── models/                    # ML models directory
│   ├── *.keras               # Neural network models
│   ├── *.joblib              # Scikit-learn models
│   └── model_comparison_results.csv
├── Dataset/                   # Training data
│   └── user_behavior_dataset.csv
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   streamlit run authai_streamlit_app.py
   ```
## 🎯 How to Use

### 1. Initial Setup
1. Navigate to `http://localhost:8501`
2. The system will auto-initialize with the best available model
3. Monitoring will start automatically

### 2. Dashboard Features
- **System Status**: Real-time monitoring status
- **Current Prediction**: Person/Robot classification
- **Confidence Score**: Model prediction confidence
- **Feature Visualization**: Live behavioral metrics
- **Prediction Timeline**: Historical trends

### 3. AuthAI Monitoring
1. System auto-initializes on startup
2. Monitor starts automatically
3. Use "Run Bot Simulator" to test detection
4. View real-time charts and metrics

### 4. Bot Simulation
- Click "🤖 Run Bot Simulator" to test the system
- Simulates 15 seconds of abnormal behavior
- System should detect and flag as "Robot"

## 🛠 Technical Details

### Behavioral Features Monitored

The system tracks:
- **Mouse Movement**: Speed and patterns
- **Keyboard Activity**: Typing speed and errors
- **Window Focus**: Application switching behavior
- **Click Patterns**: Mouse click frequency
- **Error Rates**: Backspace/correction usage

### Feature Metrics
- `avg_mouse_speed`: Average mouse movement speed (px/s)
- `avg_typing_speed`: Average typing speed (keys/min)
- `tab_switch_rate`: Window switching frequency (/min)
- `mouse_click_rate`: Mouse click frequency (/min)
- `keyboard_error_rate`: Typing error percentage (%)
- `active_window_duration`: Average window focus time (sec)

## 📊 Machine Learning Models

Supported model types:
- **Random Forest**: Tree-based ensemble method
- **XGBoost**: Gradient boosting framework
- **Neural Networks**: LSTM and Transformer models
- **Isolation Forest**: Anomaly detection
- **Autoencoder**: Deep learning anomaly detection

## 🔧 Configuration

### Detection Settings

Edit `authai_core.py` to modify detection parameters:

```python
DETECTION_INTERVAL = 5.0   # seconds between predictions
WINDOW_SECONDS = 30.0      # sliding window for statistics
CLASSIFIER_THRESHOLD = 0.5  # bot detection threshold
```

### Model Settings
- Models are automatically loaded from the `models/` directory
- Scaler is automatically loaded if available
- System uses the best performing model by default

## 🌐 Streamlit Cloud Deployment

### Prerequisites for Deployment
1. All models must be in the `models/` directory
2. Remove any local file dependencies
3. Ensure all requirements are in `requirements.txt`

### Deployment Steps
1. Push code to GitHub repository
2. Connect Streamlit Cloud to your repository
3. Select `authai_streamlit_app.py` as the main file
4. Deploy and monitor

### Cloud Compatibility
- Uses `authai_core_cloud.py` for cloud deployment
- Simulates behavioral data when real monitoring isn't available
- Optimized for cloud environments

## 🚨 Troubleshooting

### Model Loading Issues
- **Check Models Directory**: Ensure ML models are present
- **Dependencies**: Verify TensorFlow/Scikit-learn installation
- **File Permissions**: Check read permissions on model files

### Performance Issues
- **Reduce Detection Interval**: Lower frequency for better performance
- **Memory Usage**: Monitor for large datasets
- **Browser Performance**: Close unnecessary tabs

### Permission Issues
- **Windows**: May need administrator privileges for input monitoring
- **macOS**: Grant accessibility permissions
- **Linux**: Ensure X11/Wayland permissions

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎮 Interactive Features

### Real-time Visualization
- **Live Charts**: Updates every 2 seconds
- **Feature Plots**: Individual metric visualizations
- **Prediction Timeline**: Historical trend analysis
- **Alert System**: Visual and audio bot detection alerts

### Bot Detection Alerts
- **Visual Indicators**: Red alerts with robot icons
- **Confidence Display**: Shows detection confidence
- **Security Actions**: Lock account or report false positive options
- **Alert Counter**: Tracks total bot detections

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🔮 Future Enhancements

- [ ] Advanced behavioral analytics
- [ ] Additional ML model support
- [ ] API endpoints
- [ ] Mobile compatibility
- [ ] Advanced visualization
- [ ] Custom alert thresholds
- [ ] Export functionality
- [ ] Multi-user support

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review model documentation
- Open an issue on GitHub

---

**AuthAI** - Intelligent behavioral monitoring for enhanced security 🛡️
