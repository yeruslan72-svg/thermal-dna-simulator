# 🏭 AVCS DNA Industrial Monitor v6.0

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://thermal-dna-simulator.streamlit.app)
![Python Version](https://img.shields.io/badge/python-3.9-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Active Vibration Control System with AI-Powered Predictive Maintenance.

## 📋 Overview

Real-time industrial monitoring system with AI analytics and active vibration control. Tracks vibrations, temperature, and acoustic noise, predicts failures, and automatically adjusts MR dampers.

## ✨ Features

- 📊 **Real-time Monitoring**: Vibration, temperature, noise sensors
- 🤖 **AI Analytics**: Isolation Forest anomaly detection
- 🎛️ **Active Control**: MR dampers with adaptive force
- ⚠️ **Predictive Maintenance**: Risk index & RUL estimation
- 🚨 **Multi-level Alerts**: Standby, Normal, Warning, Critical

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/thermal-dna-simulator.git
cd thermal-dna-simulator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Run the application
streamlit run app.py
# Build image
docker build -t avcs-dna .

# Run container
docker run -p 8501:8501 avcs-dna
GitHub Codespaces
Click the button below to start coding instantly:

https://github.com/codespaces/badge.svg

🏗️ System Architecture
Sensors
4x Vibration Sensors (PCB 603C01) - 0-10 mm/s

4x Thermal Sensors (FLIR A500f) - 0-150°C

1x Acoustic Sensor (NI 9234) - 30-120 dB

Actuators
4x MR Dampers (LORD RD-8040) - 0-8000N

AI Model
Isolation Forest (200 estimators)

Multi-sensor data fusion

Real-time anomaly detection

📊 Dashboard Sections
Section	Description
📈 Vibration	4-channel vibration tracking
🌡️ Thermal	Temperature across components
🔊 Acoustic	Noise levels monitoring
🎛️ Dampers	Real-time force control
🤖 AI Fusion	Risk index & predictions
⚙️ Configuration
Sensor Limits
Sensor	Normal	Warning	Critical
Vibration	< 2.0 mm/s	< 4.0 mm/s	< 6.0 mm/s
Temperature	< 70°C	< 85°C	< 100°C
Noise	< 70 dB	< 85 dB	< 100 dB
Damper Forces
Mode	Force
🟢 Standby	500 N
✅ Normal	1000 N
⚠️ Warning	4000 N
🚨 Critical	8000 N
🔄 Simulation Phases
Normal Operation (0-30 cycles): Baseline readings

Gradual Degradation (30-60 cycles): Increasing values

Critical Condition (60-100 cycles): High alert state

📈 Output Metrics
Risk Index: 0-100 scale

AI Confidence: Anomaly detection confidence

RUL: Remaining Useful Life in hours

System Status: Color-coded operational state

🛠️ Technology Stack
Component	Technology
Frontend	Streamlit
ML	scikit-learn (Isolation Forest)
Visualization	Plotly
Data Processing	pandas, numpy
Configuration	python-dotenv
Container	Docker

thermal-dna-simulator/
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── .env.example          # Environment example
├── .gitignore            # Git ignore rules
├── README.md             # Documentation
├── licence               # MIT license
│
├── .devcontainer/        # GitHub Codespaces config
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── *.sh
│
├── .streamlit/           # Streamlit config
│   └── config.toml
│
├── modules/              # Core modules
│   ├── config.py
│   ├── data_manager.py
│   ├── ai_model.py
│   ├── sensor_simulator.py
│   ├── alert_system.py
│   └── ui_components.py
│
└── utils/                # Utilities
    ├── logger.py
    └── helpers.py

💡 Business Value
Metric	Value
System Cost	$250,000
Typical ROI	>2000%
Payback Period	<3 months
MTBF	8760 hours
🚨 Alert Levels
Level	Risk	Color	Action
🟢 Standby	<20%	Blue	Monitor
✅ Normal	20-50%	Green	Normal operation
⚠️ Warning	50-80%	Orange	Schedule maintenance
🚨 Critical	>80%	Red	Immediate action

# Run tests
pytest tests/

# With coverage
pytest --cov=modules tests/

# Linting
flake8 modules/
black modules/

🤝 Contributing
Fork the repository

Create feature branch (git checkout -b feature/amazing)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing)

Open Pull Request

📝 License
MIT License - see LICENSE file

👥 Authors
Yeruslan Technologies - Industrial Monitoring Solutions

Website: https://yeruslan.com

Email: info@yeruslan.com

GitHub: @yeruslan72-svg

🙏 Acknowledgments
PCB Piezotronics for vibration sensor specs

FLIR for thermal imaging technology

LORD Corporation for MR damper specifications

Streamlit for amazing framework

📞 Support
Documentation: docs.yeruslan.com

Issues: GitHub Issues

Email: support@yeruslan.com

Made with ❤️ by Yeruslan Technologies

## 📄 **6. licence** (MIT License)

```txt
MIT License

Copyright (c) 2024 Yeruslan Technologies

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
