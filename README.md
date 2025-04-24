# Telegram Bot for Vape Shop

This is a Telegram bot for selling disposable vapes (одноразки) with products like Waka, Elf Bar, and HQD.

## Setup

1. Install Python 3.7 or higher
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a new bot using [@BotFather](https://t.me/BotFather) on Telegram
4. Copy the bot token and paste it in the `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
5. Run the bot:
   ```
   python bot.py
   ```

## Features

- Browse different vape brands (Waka, Elf Bar, HQD)
- View available flavors and prices
- Easy navigation with inline buttons
- Contact information for orders

## Customization

You can customize the products, prices, and flavors by editing the `PRODUCTS` dictionary in `bot.py`.

## Security

- Keep your bot token secure and never share it
- The `.env` file is included in `.gitignore` to prevent accidental token exposure 