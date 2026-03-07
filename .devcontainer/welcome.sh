#!/bin/bash
# .devcontainer/welcome.sh

clear
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     █████╗ ██╗   ██╗ ██████╗███████╗    ██████╗ ███╗   ██╗ █████╗ 
║    ██╔══██╗██║   ██║██╔════╝██╔════╝    ██╔══██╗████╗  ██║██╔══██╗
║    ███████║██║   ██║██║     ███████╗    ██║  ██║██╔██╗ ██║███████║
║    ██╔══██║╚██╗ ██╔╝██║     ╚════██║    ██║  ██║██║╚██╗██║██╔══██║
║    ██║  ██║ ╚████╔╝ ╚██████╗███████║    ██████╔╝██║ ╚████║██║  ██║
║    ╚═╝  ╚═╝  ╚═══╝   ╚═════╝╚══════╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
║                                                              ║
║            INDUSTRIAL MONITOR SYSTEM v6.0                    ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   🚀 Quick Start:                                            ║
║   ---------------------------------------------------------- ║
║   • Run app:    streamlit run app.py                         ║
║   • Test:       pytest tests/                                ║
║   • Format:     black .                                      ║
║   • Lint:       flake8                                       ║
║                                                              ║
║   📂 Important Paths:                                         ║
║   ---------------------------------------------------------- ║
║   • Data:       /workspace/data                              ║
║   • Logs:       /workspace/logs                              ║
║   • Models:     /workspace/models                            ║
║                                                              ║
║   🔧 Useful Commands:                                         ║
║   ---------------------------------------------------------- ║
║   • status:     Check system status                          ║
║   • logs:       View application logs                        ║
║   • reset:      Reset all data                               ║
║                                                              ║
║   🌐 Streamlit will be available at:                          ║
║   http://localhost:8501                                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

# Show versions
echo -e "\n📊 Environment:"
echo "   Python: $(python --version | cut -d' ' -f2)"
echo "   Working Dir: $(pwd)"
echo "   Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "\n✅ Ready to develop! Type 'streamlit run app.py' to start\n"
