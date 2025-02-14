#!/usr/bin/env python3
import argparse
import random
import string
import threading
import concurrent.futures
import requests
from rich.console import Console
from rich.text import Text

console = Console(record=True)
WEBHOOK_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=20)

PALETTE = {
    "success": "#1aaf7c",
    "error": "#ff705c",
    "warning": "#a17fff",
    "text": "#f8f8f2"
}

WEBHOOK_URL = "PUT YOUR WEBHOOK HERE"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
]
EXTENSIONS = [
    "jpg", "jpeg", "png", "gif", "bmp", "webp",
    "mp4", "webm", "mov", "avi", "pdf", "txt",
    "mp3", "wav"
]

def generate_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

def send_to_webhook(content, filename: str) -> None:
    WEBHOOK_EXECUTOR.submit(
        lambda: requests.post(
            WEBHOOK_URL,
            files={"file": (filename, content)},
            timeout=10,
            headers={"User-Agent": random.choice(USER_AGENTS)}
        )
    )

def scanner_thread(base_url: str) -> None:
    session = requests.Session()
    while True:
        url = f"{base_url}{generate_id()}.{random.choice(EXTENSIONS)}"
        try:
            response = session.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10, stream=True)
            status = response.status_code
            txt = Text()
            if status == 200:
                txt.append("[✓] FOUND: ", style=f"bold {PALETTE['success']}")
                txt.append(url, style=f"{PALETTE['success']} underline")
                send_to_webhook(response.content, url.split("/")[-1])
            elif 400 <= status < 500:
                txt.append("[⚡] RETRY: ", style=f"bold {PALETTE['warning']}")
                txt.append(url, style=f"{PALETTE['warning']} dim")
            else:
                txt.append("[✗] MISSING: ", style=f"bold {PALETTE['error']}")
                txt.append(url, style=f"{PALETTE['error']} strike")
            console.print(txt)
            response.close()
        except Exception as e:
            console.print(Text("[⚠] ERROR: ", style=f"bold {PALETTE['warning']}") + Text(f"{url} ({str(e)})", style=f"{PALETTE['text']} dim"))

def main() -> None:
    parser = argparse.ArgumentParser(description="Catbox.moe scraper")
    parser.add_argument("threads", type=int, help="Number of concurrent threads")
    parser.add_argument("--base_url", default="https://files.catbox.moe/", help="Base target URL")
    args = parser.parse_args()
    args.base_url = args.base_url.rstrip("/") + "/"
    console.print(f"\n[bold {PALETTE['success']}]🚀 Starting [bold white]{args.threads}[/] threads with base URL [underline]{args.base_url}[/][/]\n", highlight=False)
    for _ in range(args.threads):
        threading.Thread(target=scanner_thread, args=(args.base_url,), daemon=True).start()
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        console.print(f"\n[bold {PALETTE['warning']}]🛑 Shutting down...[/]")
        WEBHOOK_EXECUTOR.shutdown(wait=True)

if __name__ == "__main__":
    main()
