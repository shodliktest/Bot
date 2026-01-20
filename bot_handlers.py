from database import update_user, update_stats # Import qilamiz

# Start bosilganda:
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    # Eski log funksiya o'rniga yangisi:
    update_user(m.from_user) 
    # ... qolgan kodlar ...

# Fayl tahlil bo'lganda (start_process ichida):
async def start_process(call: types.CallbackQuery):
    # ... tahlil tugagach ...
    
    # Statistikaga qo'shish:
    f_type = user_data[chat_id]['type'] # 'video' yoki 'audio'
    fmt = data.get('view') # 'txt' yoki 'chat' (buni to'g'irlab yuborasiz kodingizga qarab)
    
    update_stats(f_type, "txt" if fmt == "txt" else "chat")
  
