import logging
import requests
import os
import subprocess
import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass
from apscheduler.schedulers.background import BlockingScheduler
import shutil
import time
from collections import Counter

# Configuration Loader
@dataclass
class Config:
    mail_queue_threshold: int
    server_load_threshold: float
    telegram_api: str
    telegram_chat_id: str
    monitoring_interval: int
    sleep_duration: int
    http_timeout: int
    host_prefix: str
    host_suffix: str
    host_file: str
    test_mode: bool

class ConfigLoader:
    @staticmethod
    def load_config():
        logging.info("Loading configuration...")
        return Config(
            mail_queue_threshold=500,
            server_load_threshold=10,
            telegram_api="6974881789:AAHFWPEKM52FuCFXPB_rH3t7LcqGBOxc6LY",
            telegram_chat_id="-4065529233",
            monitoring_interval=3,
            sleep_duration=5,
            http_timeout=20,
            host_file="host.names"
            test_mode=true
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
                return f"Health check failed for {url}: HTTP {response.status_code}"

            data = response.json()
            alert_message = []

            # Ensure required keys exist
            if "mysql" not in data:
                alert_message.append(f"{url}: Missing 'mysql' status in response")
                mysql_status = "UNKNOWN"
            else:
                mysql_status = data["mysql"]

            if "mailqueue" not in data:
                alert_message.append(f"{url}: Missing 'mailqueue' count in response")
                mail_queue = -1  # Use an invalid value to indicate an issue
            else:
                mail_queue = data["mailqueue"]
            
            if "load" not in data:
                alert_message.append(f"{url}: Missing 'load' average in response")
                load_avg = -1  # Use an invalid value to indicate an issue
            else:
                mail_queue = data["mailqueue"]

            # Check for failures
            if "FAIL" in mysql_status:
                alert_message.append(f"{url}: MySQL issue detected: {mysql_status}")

            if mail_queue > self.config.mail_queue_threshold:
                alert_message.append(f"{url}: Mail queue too large: {mail_queue}")
            
            if load_avg > self.config.mail_queue_threshold:
                alert_message.append(f"{url}: Load average too high: {mail_queue}")

            if alert_message:
                return " | ".join(alert_message)

        except requests.exceptions.RequestException as e:
            logging.error(f"Health check request failed for {url}: {e}")
            return f"Health check request failed for {url}: {e}"
        
        return None  # No issues found


# Main Application
class MonitoringTool:
    def __init__(self):
        logging.info("Initializing MonitoringTool...")
        self.config = ConfigLoader.load_config()
        self.monitor = Monitor(self.config)
        self.scheduler = BlockingScheduler()

    def run_checks(self):
        logging.info("Running monitoring checks...")
        for host in self.monitor.hosts:
            health_alert = self.monitor.check_health_endpoint(host)
            if health_alert:
                logging.info("Sending health check alert via telegram...")
                self.send_telegram(health_alert)

    def send_telegram(self, message):
        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_api}/sendMessage"
            payload = {"chat_id": self.config.telegram_chat_id, "text": message}
            requests.post(url, json=payload)
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")

    def start(self):
        logging.info("Starting MonitoringTool scheduler...")
        self.scheduler.add_job(self.run_checks, 'interval', minutes=self.config.monitoring_interval)
        self.run_checks()
        self.scheduler.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting the MonitoringTool application...")
    tool = MonitoringTool()
    try:
        tool.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down the MonitoringTool...")
        tool.scheduler.shutdown()
