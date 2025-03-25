# cPsentry 🛡️  
**Automated Monitoring & Security Tool for cPanel Servers**

cPsentry is a lightweight monitoring and infrastructure protection tool tailored for **cPanel-based Linux servers**. It gathers real-time system information via PHP endpoints and uses a Python-based monitoring server to process metrics and take actions such as alerting, logging, or blocking abusive IPs.

### ✨ Key Features

- 📡 Real-time metrics collection via PHP endpoints on each monitored server  
- 🐍 Python-based monitoring server running as a `systemd` service  
- 🔍 Monitors:
  - Mail queue volume  
  - Apache service health  
  - MySQL database availability  
  - Filesystem usage  
  - SMTP traffic (volume & spikes)  
- 🚨 Telegram alerts for critical thresholds  
- 🔒 Automated IP blocking via iptables for spam/bot or abuse behavior  
- 🔧 Built with **Flask**, **PHP**, and **Bash scripting**

### 🔧 Installation & Usage (WIP)

Installation and configuration will be automated via a **Bash installer script** (coming soon). For now, the system requires:

- Root access on the monitoring server  
- PHP access on the target cPanel machines  
- Python 3 environment with Flask  
- Telegram Bot token and chat ID

## 📦 Tech Stack

- **Python 3** (Monitoring Server)  
- **Flask** (API Server)  
- **PHP** (Remote metric endpoints)  
- **systemd** (Daemonization)  
- **iptables** (Abuse prevention)  
- **Telegram Bot API** (Real-time alerts)  
- **Bash** (Custom instalation Script)
  
## 🔜 Upcoming

I’m currently working on integrating [**VMSentry**](https://github.com/lulubas/vmsentry) — a monitoring agent for **KVM hypervisors** — directly into cPsentry, allowing unified monitoring of both shared hosting and VPS infrastructures in a single service.

This will include:
- KVM VM-level resource tracking  
- Abuse/spam behavior detection  
- Firewall rule automation across hypervisors

---

## 📬 Contact

Built and maintained by [@louis-bastien](https://github.com/louis-bastien)

Feel free to open an issue or reach out via [LinkedIn](https://www.linkedin.com/in/louisbastien) if you'd like to collaborate or discuss improvements.
