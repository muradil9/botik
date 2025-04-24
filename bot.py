import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from config import ADMIN_USER_ID, ADMIN_USERNAME, PENDING_ORDERS

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Products database
PRODUCTS = {
    'waka': {
        'name': 'Waka',
        'flavors': {
            'waka_blueberry': {'name': 'Blueberry Ice', 'price_kzt': 10000, 'price_usdt': 19},
            'waka_mango': {'name': 'Mango Ice', 'price_kzt': 10000, 'price_usdt': 19},
            'waka_strawberry': {'name': 'Strawberry Ice', 'price_kzt': 10000, 'price_usdt': 19},
        }
    },
    'elfbar': {
        'name': 'Elf Bar',
        'flavors': {
            'elfbar_watermelon': {'name': 'Watermelon Ice', 'price_kzt': 8000, 'price_usdt': 15},
            'elfbar_grape': {'name': 'Grape Ice', 'price_kzt': 8000, 'price_usdt': 15},
            'elfbar_peach': {'name': 'Peach Ice', 'price_kzt': 8000, 'price_usdt': 15},
        }
    },
    'hqd': {
        'name': 'HQD',
        'flavors': {
            'hqd_kiwi': {'name': 'Kiwi Passion', 'price_kzt': 7000, 'price_usdt': 13},
            'hqd_banana': {'name': 'Banana Ice', 'price_kzt': 7000, 'price_usdt': 13},
            'hqd_melon': {'name': 'Melon Ice', 'price_kzt': 7000, 'price_usdt': 13},
        }
    }
}

# Store user orders and states
user_orders = {}
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    logger.info("User started the bot")
    user_id = update.message.from_user.id
    user_states[user_id] = 'start'
    
    keyboard = [
        [InlineKeyboardButton("Waka", callback_data='waka')],
        [InlineKeyboardButton("Elf Bar", callback_data='elfbar')],
        [InlineKeyboardButton("HQD", callback_data='hqd')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Добро пожаловать в магазин одноразок! Выберите бренд:',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages."""
    user_id = update.message.from_user.id
    text = update.message.text
    logger.info(f"Received message from user {user_id}: {text}")
    
    if user_id not in user_states:
        user_states[user_id] = 'start'
        await start(update, context)
        return
    
    if user_states[user_id] == 'waiting_address':
        logger.info(f"Processing address for user {user_id}")
        if user_id not in user_orders:
            user_orders[user_id] = {}
        user_orders[user_id]['address'] = text
        user_states[user_id] = 'waiting_phone'
        await update.message.reply_text(
            'Пожалуйста, введите ваш номер телефона в формате: +7XXXXXXXXXX'
        )
    elif user_states[user_id] == 'waiting_phone':
        logger.info(f"Processing phone for user {user_id}")
        if not text.startswith('+7') or len(text) != 12:
            await update.message.reply_text(
                'Пожалуйста, введите корректный номер телефона в формате: +7XXXXXXXXXX'
            )
            return
        
        user_orders[user_id]['phone'] = text
        order_id = f"order_{user_id}_{len(PENDING_ORDERS)}"
        PENDING_ORDERS[order_id] = {
            'user_id': user_id,
            'order': user_orders[user_id].copy(),
            'status': 'waiting_payment'
        }
        logger.info(f"Created order {order_id} for user {user_id}")
        
        order = user_orders[user_id]
        await update.message.reply_text(
            f"Ваш заказ:\n"
            f"Товар: {order['product_name']}\n"
            f"Цена: {order['price_kzt']}₸ / {order['price_usdt']} USDT\n"
            f"Адрес: {order['address']}\n"
            f"Телефон: {order['phone']}\n\n"
            f"Для оплаты переведите {order['price_usdt']} USDT на адрес:\n"
            f"USDT (TRC20): TYJgFhJQqXZJXJXJXJXJXJXJXJXJX\n\n"
            f"После оплаты дождитесь проверки администратора."
        )
        
        # Notify admin
        admin_keyboard = [
            [InlineKeyboardButton("Проверить оплату", callback_data=f'check_{order_id}')],
            [InlineKeyboardButton("Отклонить заказ", callback_data=f'reject_{order_id}')]
        ]
        admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)
        
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"Новый заказ!\n"
                 f"ID заказа: {order_id}\n"
                 f"Пользователь: @{update.message.from_user.username}\n"
                 f"Товар: {order['product_name']}\n"
                 f"Цена: {order['price_kzt']}₸ / {order['price_usdt']} USDT\n"
                 f"Адрес: {order['address']}\n"
                 f"Телефон: {order['phone']}\n\n"
                 f"Ожидает проверки оплаты.",
            reply_markup=admin_reply_markup
        )
        
        user_states[user_id] = 'start'
    else:
        await start(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    logger.info(f"Button pressed by user {user_id}: {data}")

    if data in PRODUCTS:
        # Show flavors for selected brand
        keyboard = []
        for flavor_id, flavor_info in PRODUCTS[data]['flavors'].items():
            keyboard.append([InlineKeyboardButton(
                f"{flavor_info['name']} - {flavor_info['price_kzt']}₸ / {flavor_info['price_usdt']} USDT",
                callback_data=flavor_id
            )])
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Выберите вкус {PRODUCTS[data]['name']}:",
            reply_markup=reply_markup
        )
    elif data == 'back':
        # Return to main menu
        keyboard = [
            [InlineKeyboardButton("Waka", callback_data='waka')],
            [InlineKeyboardButton("Elf Bar", callback_data='elfbar')],
            [InlineKeyboardButton("HQD", callback_data='hqd')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='Выберите бренд:',
            reply_markup=reply_markup
        )
    elif data.startswith('complete_'):
        # User completing order after admin verification
        try:
            order_id = data[9:]  # Remove 'complete_' prefix
            logger.info(f"User {user_id} completing order {order_id}")
            if order_id in PENDING_ORDERS and PENDING_ORDERS[order_id]['status'] == 'verified':
                order = PENDING_ORDERS[order_id]
                delivery_time = random.randint(60, 120)
                
                await query.edit_message_text(
                    f"Ваш заказ принят!\n"
                    f"Товар: {order['order']['product_name']}\n"
                    f"Цена: {order['order']['price_kzt']}₸ / {order['order']['price_usdt']} USDT\n"
                    f"Адрес: {order['order']['address']}\n"
                    f"Телефон: {order['order']['phone']}\n\n"
                    f"Примерное время доставки: {delivery_time} минут\n"
                    f"Пожалуйста, ожидайте."
                )
                del PENDING_ORDERS[order_id]
            else:
                logger.warning(f"Order {order_id} not found or not verified")
                await query.answer("Заказ не найден или не подтвержден администратором")
        except Exception as e:
            logger.error(f"Error completing order: {e}")
            await query.answer("Произошла ошибка при завершении заказа")
    elif data.startswith('check_'):
        # Admin checking payment
        if user_id == ADMIN_USER_ID:
            try:
                order_id = data[6:]  # Remove 'check_' prefix
                logger.info(f"Admin {user_id} checking order {order_id}")
                if order_id in PENDING_ORDERS:
                    order = PENDING_ORDERS[order_id]
                    order['status'] = 'verified'
                    
                    # Notify user that they can now complete the order
                    keyboard = [
                        [InlineKeyboardButton("Подтвердить заказ", callback_data=f'complete_{order_id}')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=order['user_id'],
                        text=f"Администратор проверил вашу оплату!\n"
                             f"Нажмите кнопку 'Подтвердить заказ' для завершения.",
                        reply_markup=reply_markup
                    )
                    
                    # Notify admin
                    await query.edit_message_text(
                        f"Заказ {order_id} проверен. Ожидаем подтверждения от пользователя."
                    )
            except Exception as e:
                logger.error(f"Error processing admin check: {e}")
                await query.answer("Произошла ошибка при обработке заказа")
    elif data.startswith('reject_'):
        # Admin rejecting order
        if user_id == ADMIN_USER_ID:
            try:
                order_id = data[7:]  # Remove 'reject_' prefix
                logger.info(f"Admin {user_id} rejecting order {order_id}")
                if order_id in PENDING_ORDERS:
                    order = PENDING_ORDERS[order_id]
                    # Notify user
                    await context.bot.send_message(
                        chat_id=order['user_id'],
                        text="Ваш заказ отклонен администратором. "
                             "Пожалуйста, свяжитесь с администратором для уточнения деталей."
                    )
                    # Notify admin
                    await query.edit_message_text(
                        f"Заказ {order_id} отклонен и пользователь уведомлен."
                    )
                    # Remove from pending orders
                    del PENDING_ORDERS[order_id]
            except Exception as e:
                logger.error(f"Error processing admin reject: {e}")
                await query.answer("Произошла ошибка при обработке заказа")
    else:
        # Handle flavor selection
        for brand, brand_info in PRODUCTS.items():
            if data in brand_info['flavors']:
                flavor = brand_info['flavors'][data]
                if user_id not in user_orders:
                    user_orders[user_id] = {}
                user_orders[user_id].update({
                    'product_name': f"{brand_info['name']} - {flavor['name']}",
                    'price_kzt': flavor['price_kzt'],
                    'price_usdt': flavor['price_usdt']
                })
                logger.info(f"User {user_id} selected flavor: {flavor['name']}")
                
                user_states[user_id] = 'waiting_address'
                await query.message.reply_text(
                    text=f"Вы выбрали: {flavor['name']}\n"
                         f"Цена: {flavor['price_kzt']}₸ / {flavor['price_usdt']} USDT\n\n"
                         f"Пожалуйста, введите адрес доставки:"
                )

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 