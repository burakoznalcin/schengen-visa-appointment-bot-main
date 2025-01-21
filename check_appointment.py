#!/usr/bin/env python3
"""
Schengen Visa Appointment Check Program
"""

import os
import sys
import logging
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram.ext import Application

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Telegram bot setup
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

API_URL = "https://api.schengenvisaappointments.com/api/visa-list/?format=json"

# Ülke isimleri sözlüğü
COUNTRIES_TR = {
    'France': 'Fransa',
    'Netherlands': 'Hollanda',
    'Ireland': 'İrlanda',
    'Malta': 'Malta',
    'Sweden': 'İsveç',
    'Czechia': 'Çekya',
    'Croatia': 'Hırvatistan',
    'Bulgaria': 'Bulgaristan',
    'Finland': 'Finlandiya',
    'Slovenia': 'Slovenya',
    'Denmark': 'Danimarka',
    'Norway': 'Norveç',
    'Estonia': 'Estonya',
    'Lithuania': 'Litvanya',
    'Luxembourg': 'Lüksemburg',
    'Ukraine': 'Ukrayna',
    'Latvia': 'Letonya'
}

# Ay isimleri sözlüğü
MONTHS_TR = {
    1: 'Ocak',
    2: 'Şubat',
    3: 'Mart',
    4: 'Nisan',
    5: 'Mayıs',
    6: 'Haziran',
    7: 'Temmuz',
    8: 'Ağustos',
    9: 'Eylül',
    10: 'Ekim',
    11: 'Kasım',
    12: 'Aralık'
}

def format_date(date_str):
    """Tarihi formatla: YYYY-MM-DD -> DD Month YYYY"""
    try:
        year, month, day = map(int, date_str.split('-'))
        return f"{day} {MONTHS_TR[month]} {year}"
    except:
        return date_str  # Hata durumunda orijinal tarihi döndür

class AppointmentChecker:
    def __init__(self):
        self.country = None
        self.city = None
        self.frequency = None
        self.application = None
        self.running = False
        self.task = None
        if TELEGRAM_BOT_TOKEN:
            self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    def set_parameters(self, country, city, frequency):
        """Parametreleri güncelle"""
        self.country = country
        self.city = city
        self.frequency = frequency

    async def stop(self):
        """Programı durdur"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.application:
            await self.application.shutdown()

    async def start_checking(self):
        """Kontrolleri başlat"""
        if self.application:
            await self.application.initialize()
        
        self.running = True
        while self.running:
            try:
                await self.check_appointments()
                await asyncio.sleep(self.frequency * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Kontrol sırasında hata: {str(e)}")
                await asyncio.sleep(5)  # Hata durumunda 5 saniye bekle

    async def send_notification(self, message):
        """Bildirim gönder"""
        logger.info(message)
        
        if self.application and TELEGRAM_CHAT_ID:
            try:
                await self.application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            except Exception as e:
                logger.error(f"Telegram bildirimi gönderilemedi: {str(e)}")

    async def check_appointments(self):
        """API'den randevu kontrolü yap"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as response:
                    if response.status != 200:
                        raise Exception(f"API yanıt vermedi: {response.status}")
                    
                    appointments = await response.json()
                    available_appointments = []
                    
                    for appointment in appointments:
                        # Randevu tarihi kontrolü
                        appointment_date = appointment.get('appointment_date')
                        if not appointment_date:
                            continue  # Randevu tarihi yoksa diğer kontrollere geçme
                        
                        if (appointment['source_country'] == 'Turkiye' and 
                            appointment['mission_country'].lower() == self.country.lower() and 
                            self.city.lower() in appointment['center_name'].lower()):
                            
                            available_appointments.append({
                                'country': appointment['mission_country'],
                                'city': appointment['center_name'],
                                'date': appointment_date,
                                'category': appointment['visa_category'],
                                'subcategory': appointment['visa_subcategory'],
                                'link': appointment['book_now_link']
                            })

                    if available_appointments:
                        # Tarihe göre sırala
                        available_appointments.sort(key=lambda x: x['date'])
                        
                        for appt in available_appointments:
                            # Ülke adını Türkçeye çevir
                            country_tr = COUNTRIES_TR.get(appt['country'], appt['country'])
                            # Tarihi formatla
                            formatted_date = format_date(appt['date'])

                            message = f"🎉 {country_tr} için randevu bulundu!\n\n"
                            message += f"🏢 Merkez: {appt['city']}\n"
                            message += f"📅 Tarih: {formatted_date}\n"
                            message += f"📋 Kategori: {appt['category']}\n"
                            if appt['subcategory']:  # Alt kategori varsa ekle
                                message += f"📝 Alt Kategori: {appt['subcategory']}\n"
                            message += f"\n🔗 Randevu Linki:\n{appt['link']}"
                            
                            await self.send_notification(message)
                        
                        return True
                    
                    logger.info(f"Uygun randevu bulunamadı: {self.country} - {self.city}")
                    return False

        except Exception as e:
            error_message = f"❌ API kontrolü sırasında hata: {str(e)}"
            logger.error(error_message)
            await self.send_notification(error_message)
            return False

def get_user_input():
    """Kullanıcıdan giriş al"""
    print("\nSchengen Vize Randevu Kontrol Programı")
    print("=====================================")
    
    print("\nÜlke seçimi yapın (1-17):")
    countries = {
        1: 'France',
        2: 'Netherlands',
        3: 'Ireland',
        4: 'Malta',
        5: 'Sweden',
        6: 'Czechia',
        7: 'Croatia',
        8: 'Bulgaria',
        9: 'Finland',
        10: 'Slovenia',
        11: 'Denmark',
        12: 'Norway',
        13: 'Estonia',
        14: 'Lithuania',
        15: 'Luxembourg',
        16: 'Ukraine',
        17: 'Latvia'
    }
    
    for num, country in countries.items():
        print(f"{num}. {COUNTRIES_TR[country]}")
    
    while True:
        try:
            country_choice = int(input("\nSeçiminiz (1-17): "))
            if 1 <= country_choice <= 17:
                selected_country = countries[country_choice]
                break
            print("Lütfen 1-17 arasında bir sayı girin!")
        except ValueError:
            print("Lütfen geçerli bir sayı girin!")
    
    # Şehir seçimi
    cities = {
        '1': 'Ankara',
        '2': 'Istanbul',
        '3': 'Izmir',
        '4': 'Antalya',
        '5': 'Gaziantep',
		'6': 'Bursa',
		'7': 'Antalya',
		'8': 'Edirne',
    }
    
    print("\nŞehir seçimi yapınız:")
    for key, value in cities.items():
        print(f"{key}. {value}")
    
    city_choice = input("\nSeçiminiz (1-5): ")
    selected_city = cities.get(city_choice)
    
    if not selected_city:
        raise ValueError("Geçersiz şehir seçimi!")
    
    # Kontrol sıklığı
    print("\nKontrol sıklığı (dakika):")
    frequency = int(input("Kaç dakikada bir kontrol edilsin? (1-60): "))
    if frequency < 1 or frequency > 60:
        raise ValueError("Geçersiz kontrol sıklığı! 1-60 dakika arası bir değer girin.")
    
    return selected_country, selected_city, frequency

async def show_menu(checker):
    """Ana menüyü göster"""
    while True:
        try:
            print("\nMenü:")
            print("1. Yeni sorgu başlat")
            print("2. Mevcut sorguyu durdur")
            print("3. Programdan çık")
            
            choice = input("\nSeçiminiz (1-3): ")
            
            if choice == '1':
                if checker.running:
                    await checker.stop()
                
                country, city, frequency = get_user_input()
                checker.set_parameters(country, city, frequency)
                print(f"\n{country} için {city} şehrinde randevu kontrolü başlatılıyor...")
                print(f"Kontrol sıklığı: {frequency} dakika")
                print("\nProgram çalışıyor... Menüye dönmek için Ctrl+C'ye basın.\n")
                
                return  # Menüden çık ve ana döngüye dön
                    
            elif choice == '2':
                if checker.running:
                    await checker.stop()
                    print("\nSorgu durduruldu.")
                else:
                    print("\nAktif sorgu bulunmuyor.")
                    
            elif choice == '3':
                if checker.running:
                    await checker.stop()
                print("\nProgram sonlandırılıyor...")
                sys.exit(0)
            else:
                print("\nGeçersiz seçim!")
                
        except KeyboardInterrupt:
            print("\nMenüden çıkılıyor...")
            return  # Menüden çık ve ana döngüye dön
        except ValueError as e:
            print(f"\nHata: {str(e)}")

async def main():
    """Ana program"""
    checker = AppointmentChecker()
    
    while True:
        try:
            # İlk sorguyu al ve başlat
            country, city, frequency = get_user_input()
            checker.set_parameters(country, city, frequency)
            print(f"\n{country} için {city} şehrinde randevu kontrolü başlatılıyor...")
            print(f"Kontrol sıklığı: {frequency} dakika")
            print("\nProgram çalışıyor... Menüye dönmek için Ctrl+C'ye basın.\n")
            
            checker.task = asyncio.create_task(checker.start_checking())
            try:
                await checker.task
            except asyncio.CancelledError:
                pass
            
        except KeyboardInterrupt:
            print("\nMenüye dönülüyor...")
            if checker.running:
                await checker.stop()
            try:
                await show_menu(checker)
            except Exception as e:
                print(f"\nMenü gösterilirken hata oluştu: {str(e)}")
        except ValueError as e:
            print(f"\nHata: {str(e)}")
            continue
        except Exception as e:
            print(f"\nBeklenmeyen hata: {str(e)}")
            if checker.running:
                await checker.stop()
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram sonlandırıldı.")
    except Exception as e:
        print(f"\nKritik hata: {str(e)}") 