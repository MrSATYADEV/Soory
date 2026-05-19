#!/usr/bin/env python3
"""
VPS Terminal Bot – Full control via Telegram
Auto‑chmod +x on itself.
"""

import os
import sys
import subprocess
import stat

# ─── AUTO CHMOD +X ─────────────────────────────────────
def ensure_executable():
    script_path = os.path.abspath(__file__)
    current_mode = os.stat(script_path).st_mode
    # Check if owner execute permission is set
    if not (current_mode & stat.S_IXUSR):
        try:
            # Add owner execute permission
            os.chmod(script_path, current_mode | stat.S_IXUSR)
            print(f"✅ Auto‑chmod +x applied to {script_path}")
        except Exception as e:
            print(f"⚠️ Could not chmod +x (may need sudo): {e}")

ensure_executable()
# ──────────────────────────────────────────────────────

# ─── AUTO INSTALL DEPENDENCIES ────────────────────────
try:
    import telegram
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("📦 Installing python-telegram-bot...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot"])
    print("✅ Dependencies installed. Restarting...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ─── CONFIG ────────────────────────────────────────────
BOT_TOKEN = "8248561991:AAF-RgCPl8damAr9AQISspTEEMtKiNtpwMw"
ALLOWED_USER_IDS = [8499514151]
DEFAULT_DIR = "/root"
current_dir = os.path.abspath(DEFAULT_DIR)
# ──────────────────────────────────────────────────────

def is_allowed(update: Update) -> bool:
    return update.effective_user.id in ALLOWED_USER_IDS

def run_cmd(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=current_dir)
        output = result.stdout + result.stderr
        if not output:
            output = "✅ Command executed (no output)."
        return output[:4000]
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ─── COMMAND HANDLERS ──────────────────────────────────
# (All handlers from previous code – unchanged)
# ──────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    await update.message.reply_text(
        "🔐 *VPS Terminal Bot*\n"
        "Use /help to see all commands.\n\n"
        f"📁 Current directory: `{current_dir}`",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    help_text = """
*Available Commands:*

🖥️ **Terminal**
/sh <command>   – Execute any shell command
/cd <path>      – Change directory
/pwd            – Show current directory
/ls / /dir      – List files in current directory

📄 **File Ops**
/cat <file>     – View file content
/download <file> – Download file to Telegram
/upload         – Reply to a document to upload it

📁 **Folder Ops**
/mkdir <name>   – Create directory
/rm <file>      – Delete file
/rmdir <folder> – Delete empty folder
/mv <src> <dst> – Move/rename
/cp <src> <dst> – Copy file/folder

🗜️ **Archive**
/zip <folder>   – Zip folder and download
/unzip <file>   – Extract zip file

📊 **System**
/stats          – Disk usage, memory, uptime
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /sh <command>")
        return
    cmd = " ".join(context.args)
    output = run_cmd(cmd)
    await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")

async def change_dir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text(f"📁 `{current_dir}`", parse_mode="Markdown")
        return
    new_path = " ".join(context.args)
    try:
        os.chdir(os.path.join(current_dir, new_path))
        global current_dir
        current_dir = os.getcwd()
        await update.message.reply_text(f"✅ Changed to `{current_dir}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def pwd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(f"📁 `{current_dir}`", parse_mode="Markdown")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    try:
        items = "\n".join(os.listdir(current_dir))
        if not items:
            items = "(empty)"
        await update.message.reply_text(f"📂 *Files:*\n\n`{items[:3500]}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def cat_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /cat <filename>")
        return
    file_path = os.path.join(current_dir, " ".join(context.args))
    try:
        with open(file_path, "r") as f:
            content = f.read(3500)
        await update.message.reply_text(f"```\n{content}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /download <filename>")
        return
    file_path = os.path.join(current_dir, " ".join(context.args))
    if not os.path.isfile(file_path):
        await update.message.reply_text("❌ File not found.")
        return
    try:
        await update.message.reply_document(document=open(file_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Reply to a document with /upload to save it.")
        return
    doc = update.message.reply_to_message.document
    file_path = os.path.join(current_dir, doc.file_name)
    try:
        file = await doc.get_file()
        await file.download_to_drive(file_path)
        await update.message.reply_text(f"✅ Uploaded `{doc.file_name}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def make_dir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /mkdir <foldername>")
        return
    folder = " ".join(context.args)
    try:
        os.mkdir(os.path.join(current_dir, folder))
        await update.message.reply_text(f"✅ Created `{folder}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def remove_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /rm <filename>")
        return
    file_path = os.path.join(current_dir, " ".join(context.args))
    try:
        os.remove(file_path)
        await update.message.reply_text(f"✅ Removed `{file_path}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def remove_dir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /rmdir <foldername>")
        return
    folder = " ".join(context.args)
    try:
        os.rmdir(os.path.join(current_dir, folder))
        await update.message.reply_text(f"✅ Removed `{folder}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def move_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /mv <src> <dst>")
        return
    src = os.path.join(current_dir, context.args[0])
    dst = os.path.join(current_dir, context.args[1])
    try:
        shutil.move(src, dst)
        await update.message.reply_text(f"✅ Moved `{src}` → `{dst}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def copy_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /cp <src> <dst>")
        return
    src = os.path.join(current_dir, context.args[0])
    dst = os.path.join(current_dir, context.args[1])
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        await update.message.reply_text(f"✅ Copied `{src}` → `{dst}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def zip_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /zip <foldername>")
        return
    folder = " ".join(context.args)
    folder_path = os.path.join(current_dir, folder)
    zip_path = folder_path + ".zip"
    try:
        shutil.make_archive(folder_path, "zip", folder_path)
        await update.message.reply_document(document=open(zip_path, "rb"))
        os.remove(zip_path)
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def unzip_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /unzip <zipfile>")
        return
    zip_path = os.path.join(current_dir, " ".join(context.args))
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(current_dir)
        await update.message.reply_text(f"✅ Extracted `{zip_path}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    disk = run_cmd("df -h")
    mem = run_cmd("free -h")
    uptime = run_cmd("uptime")
    text = f"📊 *System Stats*\n\n"
    text += f"📁 Current directory: `{current_dir}`\n\n"
    text += f"💾 *Disk:*\n```\n{disk[:2000]}\n```\n"
    text += f"🧠 *Memory:*\n```\n{mem[:2000]}\n```\n"
    text += f"⏰ *Uptime:*\n`{uptime[:500]}`"
    await update.message.reply_text(text, parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text("Unknown command. Use /help.")

# ─── MAIN ──────────────────────────────────────────────

def main():
    print("🤖 Starting VPS bot...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("sh", shell))
    app.add_handler(CommandHandler("cd", change_dir))
    app.add_handler(CommandHandler("pwd", pwd_cmd))
    app.add_handler(CommandHandler("ls", list_files))
    app.add_handler(CommandHandler("dir", list_files))
    app.add_handler(CommandHandler("cat", cat_file))
    app.add_handler(CommandHandler("download", download_file))
    app.add_handler(CommandHandler("upload", upload_file))
    app.add_handler(CommandHandler("mkdir", make_dir))
    app.add_handler(CommandHandler("rm", remove_file))
    app.add_handler(CommandHandler("rmdir", remove_dir))
    app.add_handler(CommandHandler("mv", move_file))
    app.add_handler(CommandHandler("cp", copy_file))
    app.add_handler(CommandHandler("zip", zip_folder))
    app.add_handler(CommandHandler("unzip", unzip_file))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("✅ Bot is running. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
