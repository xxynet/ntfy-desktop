# from plyer import notification
import webbrowser
from desktop_notifier import DesktopNotifier, Urgency, Button
import platform
import requests
import threading
import json
import asyncio
from pathlib import Path
import signal

def load_config(file="config.json"):
    with open(file, "r") as f:
      config_file = f.read()
    try:
        config_json = json.loads(config_file)
        return config_json
    except:
        pass

# def send_notification(title, message):
#     system = platform.system()
#     notification.notify(
#         title=title,
#         message=message,
#         app_name="ntfy",
#         app_icon="msg.ico",
#         timeout=5
#     )

async def send_notification(title, message, url=None):
    system = platform.system()

    notifier = DesktopNotifier(app_name="ntfy")
    await notifier.send(
        title=title,
        message=message,
        icon=Path("msg.ico").absolute(),
        urgency=Urgency.Critical,
        timeout=5,
        buttons=[Button(title="OPEN LINK", on_pressed= lambda: webbrowser.open(url))] if url else []
    )


def listen_to_topic(url, topic, loop):
    resp = requests.get(f"{url}/{topic}/json", stream=True)
    for line in resp.iter_lines():
        if line:
            msg_str = line.decode('utf-8')
            msg_json = json.loads(msg_str)
            event = msg_json.get("event", "")
            if event == "message":
                raw_title = msg_json.get("title", "")
                title = msg_json.get("title", f"{url.split('://')[-1]}/{topic}")
                msg = msg_json.get("message", "")
                tags = msg_json.get("tags", [])
                click_url = msg_json.get("click", "")
                if tags:
                    title_emoji = ""
                    with open("emoji.json", "r", encoding="utf-8") as f:
                        emoji_json = json.loads(f.read())
                    for i in range(len(tags)):
                        emoji = emoji_json.get(tags[i], "")
                        if emoji:
                            title_emoji += f"{emoji} "
                    if raw_title:
                        title = title_emoji + title
                    else:
                        msg = title_emoji + msg


                asyncio.run_coroutine_threadsafe(
                    send_notification(title=title, message=msg, url=click_url),
                    loop
                )
            print(msg_str)

if __name__ == "__main__":
    config_json = load_config()

    threads = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def run_loop():
        loop.run_forever()

    # Start the event loop in a separate thread
    loop_thread = threading.Thread(target=run_loop, daemon=True)
    loop_thread.start()

    for server, topics in config_json.items():
        for topic in topics:
            thread = threading.Thread(target=listen_to_topic, args=(server, topic, loop), daemon=True)
            thread.start()
            threads.append(thread)
    
    for thread in threads:
        thread.join()