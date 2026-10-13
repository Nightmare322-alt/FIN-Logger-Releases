import json
import os
import sys
import urllib.parse
import urllib.request

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "").strip()
LATEST_JSON_URL = "https://raw.githubusercontent.com/Nightmare322-alt/FIN-Logger-Releases/main/latest.json"

if not TOKEN:
    print("TELEGRAM_BOT_TOKEN is not configured")
    sys.exit(1)

API = f"https://api.telegram.org/bot{TOKEN}/"

def request_json(url, data=None):
    if data is None:
        req = urllib.request.Request(url, headers={"User-Agent": "FIN-Logger-Telegram-Bot"})
    else:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, headers={"User-Agent": "FIN-Logger-Telegram-Bot"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def tg(method, **params):
    result = request_json(API + method, params)
    if not result.get("ok"):
        raise RuntimeError(result.get("description", f"Telegram {method} failed"))
    return result.get("result")

def main_keyboard():
    return json.dumps({
        "keyboard": [
            [{"text": "🐞 Сообщить о баге"}, {"text": "💡 Предложить доработку"}],
            [{"text": "📦 Скачать последнюю версию"}, {"text": "ℹ️ Версия"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    }, ensure_ascii=False)

def send_message(chat_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    if reply_markup is not None:
        params["reply_markup"] = reply_markup
    return tg("sendMessage", **params)

def load_latest():
    return request_json(LATEST_JSON_URL)

def send_latest(chat_id):
    latest = load_latest()
    version = latest.get("version", "?")
    apk_url = latest.get("apkUrl", "")
    changelog = latest.get("changelog", "")
    if not apk_url:
        send_message(chat_id, "Последний APK пока не опубликован.")
        return
    caption = f"FIN Logger v{version}\n\n{changelog or 'Актуальная версия приложения.'}"
    try:
        tg("sendDocument", chat_id=chat_id, document=apk_url, caption=caption)
    except Exception:
        send_message(chat_id, f"{caption}\n\nСкачать APK: {apk_url}")

def feedback_kind(message):
    reply = message.get("reply_to_message") or {}
    prompt = (reply.get("text") or "").lower()
    if "опишите проблему" in prompt:
        return "BUG"
    if "опишите идею" in prompt or "опишите пожелание" in prompt:
        return "IDEA"
    return None

def forward_feedback(message, kind):
    chat_id = message["chat"]["id"]
    user = message.get("from") or {}
    username = f"@{user['username']}" if user.get("username") else "без username"
    name = " ".join(x for x in [user.get("first_name"), user.get("last_name")] if x) or "без имени"
    title = "🐞 БАГ" if kind == "BUG" else "💡 ПРЕДЛОЖЕНИЕ"
    summary = f"{title}\nПользователь: {name} ({username})\nuser_id: {user.get('id', '?')}"

    if ADMIN_CHAT_ID:
        send_message(ADMIN_CHAT_ID, summary)
        tg(
            "forwardMessage",
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=chat_id,
            message_id=message["message_id"]
        )
        send_message(
            chat_id,
            "Спасибо за обратную связь! Сообщение передано разработчику. Мы ценим, что вы помогаете улучшать FIN Logger.",
            main_keyboard()
        )
    else:
        send_message(
            chat_id,
            "Спасибо за обратную связь! Бот работает, но разработчик ещё не указал ADMIN_CHAT_ID.",
            main_keyboard()
        )

def force_reply_prompt(chat_id, text):
    markup = json.dumps({
        "force_reply": True,
        "selective": True,
        "input_field_placeholder": "Напишите сообщение…"
    }, ensure_ascii=False)
    send_message(chat_id, text, markup)

def handle_message(message):
    chat_id = message.get("chat", {}).get("id")
    if chat_id is None:
        return
    text = (message.get("text") or "").strip()

    kind = feedback_kind(message)
    if kind:
        forward_feedback(message, kind)
        return

    if text == "/start":
        send_message(
            chat_id,
            "Привет! Это бот FIN Logger. Здесь можно скачать актуальную версию приложения, сообщить о баге или предложить доработку.",
            main_keyboard()
        )
    elif text == "/myid":
        send_message(chat_id, f"Ваш Telegram chat_id: {chat_id}")
    elif text in ("/latest", "📦 Скачать последнюю версию"):
        send_message(chat_id, "Проверяю актуальную версию FIN Logger…")
        send_latest(chat_id)
    elif text in ("/version", "ℹ️ Версия"):
        latest = load_latest()
        send_message(
            chat_id,
            f"Последняя версия FIN Logger: {latest.get('version', '?')}\n\n{latest.get('changelog') or 'Без описания изменений.'}"
        )
    elif text in ("/bug", "🐞 Сообщить о баге"):
        force_reply_prompt(chat_id, "Опишите проблему одним сообщением. Можно приложить скриншот или файл.")
    elif text in ("/idea", "💡 Предложить доработку"):
        force_reply_prompt(chat_id, "Опишите идею или пожелание одним сообщением. Можно приложить скриншот или файл.")
    else:
        send_message(
            chat_id,
            "Выберите действие на клавиатуре ниже или используйте /latest, /version, /bug, /idea.",
            main_keyboard()
        )

def set_commands():
    commands = json.dumps([
        {"command": "start", "description": "Открыть меню"},
        {"command": "latest", "description": "Скачать последнюю версию"},
        {"command": "version", "description": "Показать актуальную версию"},
        {"command": "bug", "description": "Сообщить о баге"},
        {"command": "idea", "description": "Предложить доработку"},
        {"command": "myid", "description": "Показать мой chat_id"}
    ], ensure_ascii=False)
    tg("setMyCommands", commands=commands)

def main():
    set_commands()
    updates = tg("getUpdates", timeout=0, limit=100, allowed_updates=json.dumps(["message"]))
    max_update_id = None

    for update in updates:
        update_id = update.get("update_id")
        if update_id is not None:
            max_update_id = update_id if max_update_id is None else max(max_update_id, update_id)
        message = update.get("message")
        if not message:
            continue
        try:
            handle_message(message)
        except Exception as exc:
            print(f"Failed to handle update {update_id}: {exc}", file=sys.stderr)
            try:
                send_message(message["chat"]["id"], "Произошла ошибка. Попробуйте ещё раз чуть позже.")
            except Exception:
                pass

    if max_update_id is not None:
        tg("getUpdates", offset=max_update_id + 1, timeout=0, limit=1)

if __name__ == "__main__":
    main()
