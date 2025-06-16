import aiohttp.client_exceptions
from pystyle import System, Colors, Write
from aiohttp import ClientSession
import aiohttp
import os
import random
import ssl
import asyncio
import config
import re
import datetime
import fake_useragent

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROXIES_FILE_PATH = os.path.join(BASE_DIR, 'proxies.txt')
REPORTURL_PATH = os.path.join(BASE_DIR, "reporturl.txt")
ua = fake_useragent.FakeUserAgent()


def get_time_rn():
    date = datetime.datetime.now()
    hour = date.hour
    minute = date.minute
    second = date.second
    timee = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
    return timee

def Input(prompt: str, type_):
    while True:
        try:
            return type_(Write.Input(prompt, Colors.blue_to_purple, interval=0.0001))
        except ValueError: continue
def yorn(prompt: str) -> bool:
    while True:
        i = Input(prompt, str)
        if i in ["y", "yes", "1", "t"]: return True
        elif i in ["n", "no", "2", "f"]: return False
        else: continue





class ProxiesWorker:
    def __init__(self) -> None:
        self.path = PROXIES_FILE_PATH
        self.session = None
        self.sources = {
            "http": [
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http"
            ],
            "https": [
                "https://www.proxy-list.download/api/v1/get?type=https",
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/https.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https"
            ],
            "socks4": [
                "https://www.proxy-list.download/api/v1/get?type=socks4",
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4"
            ],
            "socks5": [
                "https://www.proxy-list.download/api/v1/get?type=socks5",
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5"
            ]
        }

    def write(self, content):
        try:
            with open(self.path, "a+") as file:
                file.write(f"{content}\n")
        except IOError as e:
            print(f"Error writing to file: {e}")
    def content(self):
        try:
            with open(self.path, "r") as file:
                return file.read()
        except FileNotFoundError:
            return ""
        except IOError as e:
            Write.Print(f"\n[!] Error reading proxy file: {e}", Colors.red, interval=0.0001)
            return ""
    async def load_all(self, type: str) -> list:
        if type not in self.sources:
            raise ValueError(f"Invalid proxy type: {type}")
            
        if self.session is None:
            self.session = ClientSession()
            
        proxies = []
        try:
            for url in self.sources[type]:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            # Split content into individual proxies and filter valid ones
                            proxy_list = [p.strip() for p in content.splitlines() if ":" in p]
                            proxies.extend(proxy_list)
                except Exception as e:
                    Write.Print(f"[!] Error fetching from {url}: {e}", Colors.red, interval=0.0001)
                    continue
        finally:
            if self.session:
                await self.session.close()
                self.session = None
                
        return proxies


    async def __aenter__(self):
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def test_proxies(self, proxies: list, timeout: int = 10) -> list:
        working_proxies = []
        test_url = "http://example.com"
        
        if self.session is None or self.session.closed:
            self.session = ClientSession()
        
        for proxy in proxies:
            try:
                # Handle different proxy types
                if proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                    proxy_url = proxy.strip()
                else:
                    proxy_url = f"http://{proxy.strip()}"
                    
                async with self.session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        working_proxies.append(proxy)
                    else: Write.Print(f"\n[!] Proxy {proxy} failed with status code {response.status}", Colors.yellow, interval=0.001)
            except aiohttp.ClientProxyConnectionError:
                Write.Print(f"\n[!] Failed to connect to proxy: {proxy}", Colors.red, interval=0.001)
                continue
            except Exception as e:
                Write.Print(f"\n[!] Error with {proxy}: {str(e)}", Colors.red, interval=0.001)
                continue
                
        return working_proxies
async def reconnect(url: str, session: ClientSession, max_retries: int = 3):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": ua.random
    }
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, ssl=ssl_context, headers=headers) as response:
                match_nickname = re.search(r'nickname=([^&]+)', url)
                match_user_id = re.search(r'owner_id=([^&]+)', url)
                if response.status == 200:
                    Write.Print(f"\n[*] {get_time_rn()} Successfully reported {match_nickname.group(1)}({match_user_id.group(1)})", Colors.blue_to_purple, interval=0.0001)
                    return
                else:
                    Write.Print(f"\n[!] {get_time_rn()} Report failed with status code: {response.status}", Colors.yellow, interval=0.0001)
        except aiohttp.client_exceptions.ClientConnectionError:
            if attempt < max_retries - 1:
                Write.Print(f"\n[!] {get_time_rn()} Failed to connect to TikTok servers, retrying... ({attempt + 1}/{max_retries})", Colors.red, interval=0.0001)
                await asyncio.sleep(1)  # Add delay between retries
            else:
                Write.Print(f"\n[!] {get_time_rn()} Failed to connect to TikTok servers after {max_retries} attempts", Colors.red, interval=0.0001)
        except Exception as e:
            Write.Print(f"\n[!] {get_time_rn()} Error: {str(e)}", Colors.red, interval=0.0001)
            break


async def report(url: str, proxies: list, session: ClientSession):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    proxy = random.choice(proxies)
    headers = {
        "User-Agent": ua.random
    }
    try:
        async with session.get(url, proxy=proxy, ssl=ssl_context, headers=headers) as response:
            match_nickname = re.search(r'nickname=([^&]+)', url)
            match_user_id = re.search(r'owner_id=([^&]+)', url)
            if response.status == 200: Write.Print(f"\n[*] {get_time_rn()} Succesfully reported {match_nickname.group(1)}({match_user_id.group(1)})", Colors.blue_to_purple, interval=0.0001)
            else: Write.Print(f"\n[!] {get_time_rn()} Report failed with status code: {response.status}", Colors.yellow, interval=0.0001)
    except aiohttp.client_exceptions.ClientConnectionError: 
        Write.Print(f"\n[!] {get_time_rn()} Failed to connect, reconnecting...", Colors.red, interval=0.0001)
        await reconnect(url,session)
    except Exception as e:
        Write.Print(f"\n[!] {get_time_rn()} Error: {str(e)}\n Reconnecting...", Colors.red, interval=0.0001)
        await reconnect(url,session)

async def start(url, amount, threads):
    if config.USE_PROXIES:
        proxy_worker = ProxiesWorker()

        proxies = []
        if proxy_worker.content() != "" and yorn("\n[?] There are some proxies already in the proxies.txt file. Would you like to continue with them(not recommended if you dont have paid proxies there)?(Y or N): "):
            proxies = proxy_worker.content().splitlines()
        else:
            Write.Print("\n[*] Generating proxies.... This can take some time....", Colors.blue_to_purple, interval=0.0001)
            all_pr = await proxy_worker.load_all(config.PROXY_TYPE)
            proxies = await proxy_worker.test_proxies(all_pr)
        if not proxies:
            Write.Print("\n[!] No working proxies were found!", Colors.red, interval=0.0001)
            return
        async with ClientSession() as session:
            tasks = []
            for _ in range(threads):
                thread_tasks = []
                for _ in range(amount):
                    thread_tasks.append(report(url, proxies, session))
                tasks.append(thread_tasks)
            await asyncio.gather(*tasks)
    else:
        async with ClientSession() as session:
            tasks = []
            for _ in range(threads):
                for _ in range(amount):
                    tasks.append(reconnect(url, session))
            await asyncio.gather(*tasks)
async def main():
    if not os.path.exists(PROXIES_FILE_PATH): open(PROXIES_FILE_PATH, "w").close()
    if not os.path.exists(REPORTURL_PATH): open(REPORTURL_PATH, "w").close()
    banner = """
 /$$$$$$$$ /$$ /$$    /$$$$$$$$        /$$       /$$      /$$                              /$$$$$$$                                            /$$                        
|__  $$__/|__/| $$   |__  $$__/       | $$      | $$$    /$$$                             | $$__  $$                                          | $$                        
   | $$    /$$| $$   /$$| $$  /$$$$$$ | $$   /$$| $$$$  /$$$$  /$$$$$$   /$$$$$$$ /$$$$$$$| $$  \ $$  /$$$$$$   /$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$    /$$$$$$   /$$$$$$ 
   | $$   | $$| $$  /$$/| $$ /$$__  $$| $$  /$$/| $$ $$/$$ $$ |____  $$ /$$_____//$$_____/| $$$$$$$/ /$$__  $$ /$$__  $$ /$$__  $$ /$$__  $$|_  $$_/   /$$__  $$ /$$__  $$
   | $$   | $$| $$$$$$/ | $$| $$  \ $$| $$$$$$/ | $$  $$$| $$  /$$$$$$$|  $$$$$$|  $$$$$$ | $$__  $$| $$$$$$$$| $$  \ $$| $$  \ $$| $$  \__/  | $$    | $$$$$$$$| $$  \__/
   | $$   | $$| $$_  $$ | $$| $$  | $$| $$_  $$ | $$\  $ | $$ /$$__  $$ \____  $$\____  $$| $$  \ $$| $$_____/| $$  | $$| $$  | $$| $$        | $$ /$$| $$_____/| $$      
   | $$   | $$| $$ \  $$| $$|  $$$$$$/| $$ \  $$| $$ \/  | $$|  $$$$$$$ /$$$$$$$//$$$$$$$/| $$  | $$|  $$$$$$$| $$$$$$$/|  $$$$$$/| $$        |  $$$$/|  $$$$$$$| $$      
   |__/   |__/|__/  \__/|__/ \______/ |__/  \__/|__/     |__/ \_______/|_______/|_______/ |__/  |__/ \_______/| $$____/  \______/ |__/         \___/   \_______/|__/      
                                                                                                              | $$                                                        
                                                                                                              | $$                                                        
                                                                                                              |__/                                                        
                                                            made by wndkx; tg: @wndkx; https://github.com/wndkx
"""    
    System.Clear()
    Write.Print(banner, Colors.blue_to_purple, interval=0.0001)
    Write.Print("[*] Getting report url...", Colors.blue_to_purple, interval=0.0001)
    
    try:
        with open(REPORTURL_PATH, "r") as f:
            url = f.read().strip()
    except FileNotFoundError:
        Write.Print("\n[!] Report URL file not found! Please create reporturl.txt and add the URL.", Colors.red, interval=0.0001)
        return
    except IOError as e:
        Write.Print(f"\n[!] Error reading report URL file: {e}", Colors.red, interval=0.0001)
        return
        
    if not url:
        Write.Print("\n[!] Report URL is empty! Please write it down to the text file and then restart the tool!", Colors.red, interval=0.0001)
        return
        
    try:
        threads = Input("\n[?] Please enter the amount of concurrent threads that you want to use: ", int)
        amount = Input("\n[?] Please enter the amount of requests per 1 concurrent thread: ", int)
        
        if threads <= 0 or amount <= 0:
            Write.Print("\n[!] Threads and amount must be greater than 0!", Colors.red, interval=0.0001)
            return
            
        Write.Print(f"\n[*] {get_time_rn()} Starting mass-report...", Colors.blue_to_purple, interval=0.0001)
        await start(url, amount, threads)
    except KeyboardInterrupt:
        Write.Print("\n[!] Operation cancelled by user", Colors.yellow, interval=0.0001)
    except Exception as e:
        Write.Print(f"\n[!] An unexpected error occurred: {str(e)}", Colors.red, interval=0.0001)
if __name__ == "__main__":
    asyncio.run(main())