import logging
import requests
import os
import sys
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from dataclasses import dataclass

# Configure logging (Only write to file, no console output)
LOG_FILE = "monitoring.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a")  # Append mode
    ]
)

# Configuration Loader
@dataclass
class Config:
    mail_queue_threshold: int
    server_load_threshold: float
    telegram_api: str
    telegram_chat_id: str
    monitoring_interval: int
    http_timeout: int
    host_file: str

class ConfigLoader:
    @staticmethod
    def load_config():
        logging.info("Loading configuration...")
        return Config(
            mail_queue_threshold=500,
            server_load_threshold=10,
            telegram_api="7611133288:AAGnvY6HLAD-uvGKZEF5iMlrcRymkMdWhSU",
            telegram_chat_id="6995825953",
            monitoring_interval=3,  # In minutes
            http_timeout=20,
            host_file="host.names"
        )

# Monitor Class
class Monitor:
    def __init__(self, config: Config):
        logging.info("Initializing Monitor...")
        self.config = config
        self.hosts = self.load_hosts()

    def load_hosts(self):
        if not os.path.exists(self.config.host_file):
            logging.error(f"Host file {self.config.host_file} not found.")
            return []
        with open(self.config.host_file, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def check_health_endpoint(self, url):
        logging.info(f"Checking health endpoint: {url}")
        try:
            response = requests.get(url, timeout=self.config.http_timeout)
            if response.status_code != 200:
                logging.warning(f"Health check failed for {url}: HTTP {response.status_code}")
                return {"error": f"Health check failed for {url}: HTTP {response.status_code}"}

            data = response.json()

            # Ensure required keys exist
            raw_data = {
                "mysql_status": data.get("mysql", "UNKNOWN"),
                "mail_queue": int(data.get("mailqueue", -1)) if str(data.get("mailqueue", -1)).isdigit() else -1,
                "load_avg": float(data.get("load", -1)) if str(data.get("load", -1)).replace('.', '', 1).isdigit() else -1
            }

            logging.info(f"Raw data from {url}: {json.dumps(raw_data, indent=2)}")

            alert_message = []

            if raw_data["mysql_status"] == "UNKNOWN":
                alert_message.append(f"{url}: Missing 'mysql' status in response")
            if raw_data["mail_queue"] == -1:
                alert_message.append(f"{url}: Missing 'mailqueue' count in response")
            if raw_data["load_avg"] == -1:
                alert_message.append(f"{url}: Missing 'load' average in response")

            if "FAIL" in raw_data["mysql_status"]:
                alert_message.append(f"{url}: MySQL issue detected: {raw_data['mysql_status']}")
            if raw_data["mail_queue"] > self.config.mail_queue_threshold:
                alert_message.append(f"{url}: Mail queue too large: {raw_data['mail_queue']}")
            if raw_data["load_avg"] > self.config.server_load_threshold:
                alert_message.append(f"{url}: Load average too high: {raw_data['load_avg']}")

            return {
                "alerts": " | ".join(alert_message) if alert_message else None,
                "raw_data": raw_data
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"Health check request failed for {url}: {e}")
            return {"error": f"Health check request failed for {url}: {e}"}

# Main Application
class MonitoringTool:
    def __init__(self, test_mode=False):
        logging.info(f"Initializing MonitoringTool... Test mode: {test_mode}")
        self.config = ConfigLoader.load_config()
        self.monitor = Monitor(self.config)
        self.scheduler = BlockingScheduler()
        self.test_mode = test_mode

    def run_checks(self):
        logging.info("Running monitoring checks...")
        for host in self.monitor.hosts:
            result = self.monitor.check_health_endpoint(host)

            # Extract alerts and raw data
            health_alert = result.get("alerts")
            raw_data = result.get("raw_data")

            if self.test_mode:
                message = f"🔍 Test Mode: Server Data from {host}\n{json.dumps(raw_data, indent=2)}"
                logging.info(f"Test Mode - Sending full data via Telegram for {host}")
                self.send_telegram(message)
            elif health_alert:
                logging.info(f"Sending health check alert via Telegram for {host}")
                self.send_telegram(health_alert)

        # After each check, clear old logs
        self.clear_old_logs()

    def send_telegram(self, message):
        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_api}/sendMessage"
            payload = {"chat_id": self.config.telegram_chat_id, "text": message}
            response = requests.post(url, json=payload)

            if response.status_code != 200:
                logging.error(f"Telegram API error: {response.status_code}, Response: {response.text}")
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")

    def clear_old_logs(self):
        """Deletes log entries older than 7 days without affecting new logs."""
        if not os.path.exists(LOG_FILE):
            return

        seven_days_ago = datetime.now() - timedelta(days=7)
        log_lines = []

        with open(LOG_FILE, "r") as file:
            for line in file:
                try:
                    log_timestamp = datetime.strptime(line.split(" | ")[0], "%Y-%m-%d %H:%M:%S")
                    if log_timestamp >= seven_days_ago:
                        log_lines.append(line)
                except ValueError:
                    log_lines.append(line)  # Keep any malformed lines

        # Write back only recent logs (without replacing file instantly)
        with open(LOG_FILE, "w") as file:
            file.writelines(log_lines)

    def start(self):
        logging.info(f"Starting MonitoringTool scheduler (Test Mode: {self.test_mode})...")
        self.scheduler.add_job(self.run_checks, 'interval', minutes=self.config.monitoring_interval)
        self.run_checks()  # Run immediately before scheduling starts
        self.scheduler.start()

if __name__ == "__main__":
    logging.info("Starting the MonitoringTool application...")

    test_mode = "--test" in sys.argv

    try:
        tool = MonitoringTool(test_mode)
        tool.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down the MonitoringTool...")
        tool.scheduler.shutdown()
