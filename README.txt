🛍️ Telegram Bot for Online Store Orders and Inventory

Want to manage orders and inventory directly through Telegram? This bot automates order processing and stock management!
With this bot, you can track inventory levels, manage orders, and receive notifications about product and order statuses.

✅ What does it do?

• 🛒 Displays a product catalog and allows order creation
• 📦 Manages stock levels in the inventory
• 📝 Updates order statuses (e.g., "processed," "shipped")
• 📊 Generates reports on current stock and orders
• 📂 Stores all information in a database for further analysis

🔧 Functionality

✅ Simple interface for adding products to the catalog
✅ Easy configuration of order statuses and stock levels
✅ Notifications about order statuses and low stock alerts

📩 Want to simplify order processing and inventory management?

Contact me on Telegram, and I'll help you set up this bot for your business! 🚀

# INSTRUCTIONS FOR INSTALLING AND LAUNCHING A TELEGRAM BOT

## CONTENT
1. Installation on Windows
2. Installation on Linux
3. Setting up the bot
4. Launching the bot
5. Bot Commands
6. Problem solving

---

##1. INSTALLATION ON WINDOWS

### 1.1. Installing Python 3.9
1. Download Python 3.9.13 from the official website:
https://www.python.org/downloads/release/python-3913/
   
   Select "Windows installer (64-bit)" or "Windows installer (32-bit)" depending on your system.

2. Run the downloaded installation file.

3. **IMPORTANT**: Check the box "Add Python 3.9 to PATH" before clicking on "Install Now".

4. Click "Install Now" and wait for the installation to complete.

### 1.2. Create a folder for the project
1. Create a new folder for the bot, for example, on the desktop.
   Call it "TelegramShopBot" or any other convenient name.

2. Copy the bot script file (for example, `bot.py `) to this folder.

### 1.3. Opening the command line
1. Press Win+R, type "cmd" and press Enter.

2. At the command prompt, navigate to the created folder with the bot.
   For example:
   ```
   cd C:\Users\USER_NAME\Desktop\TelegramShopBot
   ```

### 1.4. Creating a virtual environment and installing libraries
1. Run the following commands in order:

   ```
   python -m venv venv
   venv\Scripts\activate
   pip install aiogram>=3.0.0
   ```

   After executing the last command, wait for the library installation to complete.

---

## 2. INSTALLATION ON LINUX

### 2.1. Installing Python 3.9
1. Open a terminal using Ctrl+Alt+T.

2. Run the following commands to install Python 3.9:

   For Ubuntu/Debian:
   ```
   sudo apt update
   sudo apt install software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.9 python3.9-venv python3.9-dev
   ```

   For CentOS/RHEL:
``
   sudo yum install -y python39 python39-devel
   ```

### 2.2. Creating a folder for a project
1. Create a new folder for the bot:
   ```
   mkdir ~/TelegramShopBot
   cd ~/TelegramShopBot
   ```

2. Copy the bot script file (for example, `bot.py `) to this folder.

### 2.3. Creating a virtual environment and installing libraries
1. While in the project folder, run the following commands:

   ```
   python3.9 -m venv venv
   source venv/bin/activate
   pip install aiogram>=3.0.0
   ```

   After executing the last command, wait for the library installation to complete.

---

##3. SETTING UP THE BOT

### 3.1. Getting a Bot token
1. Open Telegram and find the bot @BotFather.

2. Write the /newbot command to him and follow the instructions:
   - Specify the name of the bot (for example, "My Shop Bot")
- Specify a unique username that must end with "bot" (for example, "my_shop_2024_bot")

3. After creating the bot, you will receive a token that looks something like this:
   ```
   1234567890:AAHEXaFjvmGwYAyBQIazEPpO2V0g5uRRRRR
   ```

4. Copy this token and save it.

### 3.2. Getting the Administrator ID
1. Open Telegram and find the bot @userinfobot.

2. Write him any message and he will send you your ID (number).

3. Remember or copy this ID.

### 3.3. Changing the settings in the bot file
1. Open the file with the bot code (for example, `bot.py `) in any text editor:
   - On Windows, you can use Notepad (right-click on the file → Open with → Notepad)
- On Linux, you can use the nano editor: `nano bot.py `

2. Find the following lines at the beginning of the file:
   ```python
   API_TOKEN = 'YOUR_BOT_TOKEN'
   ADMIN_ID = 123456789
   ```

3. Replace 'YOUR_BOT_TOKEN' with the copied bot token (in quotes).

4. Replace 123456789 with your ID received from @userinfobot (without quotes).

5. Save the file.

---

##4. LAUNCHING THE BOT

### 4.1. Running on Windows
1. If the command prompt is closed, open it again and navigate to the bot folder:
``
   cd C:\Users\USER_NAME\Desktop\TelegramShopBot
   ```

2. Activate the virtual environment, if it is not already activated:
``
   venv\Scripts\activate
   ```

3. Launch the bot with the command:
   ```
   python bot.py
   ```

4. The bot must start successfully. You will see the message "Launching the bot..." on the command line.

5. To stop the bot, press Ctrl+C at the command prompt.

### 4.2. Running on Linux
1. If the terminal is closed, open it again and navigate to the bot folder:
``
   cd ~/TelegramShopBot
   ```

2. Activate the virtual environment, if it is not already activated:
``
   source venv/bin/activate
   ```

3. Launch the bot with the command:
   ```
   python bot.py
   ```

4. The bot must start successfully. You will see the message "Launching the bot..." in the terminal.

5. To stop the bot, press Ctrl+C in the terminal.

### 4.3. Running the bot in the background (Linux only)
To make the bot work after closing the terminal:

1. While in the bot folder, run:
   ```
   nohup python bot.py > bot_log.txt 2>&1 &
   ```

2. To stop the bot later, find its ID.:
   ```
   ps aux | grep python
   ```

3. Find the line with "bot.py " and remember the number at the beginning of the line (PID).

4. Stop the bot with the command:
   ```
   kill PID
   ```
   Where PID is the stored number.

---

##5. BOT COMMANDS

### 5.1. Commands for all users
- `/start` - Start working with the bot
- `/catalog` - Show the product catalog
- `/order' - Create a new order
- `/status` - Check the order status

### 5.2. Commands for the administrator
- `/stock' - Inventory management of goods
- `/orders` - Viewing and managing orders

---

## 6. PROBLEM SOLVING

### 6.1. The aiogram library is not installed.
- Make sure that you have activated the virtual environment
- Try updating pip with the command:
``
  pip install --upgrade pip
  ```
- Then repeat the aiogram installation:
``
  pip install aiogram>=3.0.0
  ```

### 6.2. The bot does not start
- Check if the bot token is specified correctly.
- Make sure that you are in the folder with the bot file.
- Make sure that you have activated the virtual environment

### 6.3. Error "ModuleNotFoundError: No module named 'aiogram'"
- Make sure you have activated the virtual environment before launching the bot
- If the error persists, repeat the aiogram installation:
``
  pip install aiogram>=3.0.0
  ```

### 6.4. Other errors
If you encounter other errors, try:
1. Restart the computer
2. Create a new virtual environment and install the libraries again
3. Search for the error text in Google for more information

---

## ADDITIONAL INFORMATION
- The database and all data about products and orders are stored in the `shop.db` file, which is created automatically in the bot folder.
- When the bot is launched for the first time, a test product catalog is created.
- All logs of the bot are recorded in the console.

---

If you still have any questions, please contact the developer or the support service.
