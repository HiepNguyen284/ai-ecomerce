import random
import re
import urllib.parse
from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category, Product

USD_TO_VND_RATE = Decimal('26000')
THOUSAND = Decimal('1000')

VND_PRICE_RANGES = {
    'Điện thoại': (Decimal('5000000'), Decimal('45000000')),
    'Laptop': (Decimal('12000000'), Decimal('80000000')),
    'Âm thanh': (Decimal('300000'), Decimal('25000000')),
    'Thời trang': (Decimal('150000'), Decimal('4000000')),
    'Giày dép': (Decimal('300000'), Decimal('7000000')),
    'Gia dụng': (Decimal('800000'), Decimal('50000000')),
    'Nhà bếp': (Decimal('100000'), Decimal('15000000')),
    'Sách': (Decimal('80000'), Decimal('700000')),
    'Gaming': (Decimal('500000'), Decimal('50000000')),
    'Đồng hồ': (Decimal('500000'), Decimal('45000000')),
    'Thể thao & Fitness': (Decimal('150000'), Decimal('60000000')),
    'Làm đẹp': (Decimal('90000'), Decimal('12000000')),
}

def _round_to_thousand(value):
    rounded = (value / THOUSAND).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * THOUSAND
    return rounded.quantize(Decimal('0.01'))

def _get_price(cat_name, idx):
    min_p, max_p = VND_PRICE_RANGES[cat_name]
    step = (max_p - min_p) / 25
    price = min_p + step * Decimal(str(idx))
    return _round_to_thousand(price)

class Command(BaseCommand):
    help = 'Generate 20-25 distinct products per category with pollinations AI dynamic image'
    
    def handle(self, *args, **options):

        categories_data = {'Điện thoại': ('smartphone', ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16', 'iPhone 15 Pro Max', 'Samsung Galaxy S25 Ultra', 'Samsung Galaxy S25+', 'Samsung Galaxy S25', 'Samsung Galaxy Z Fold 6', 'Samsung Galaxy Z Flip 6', 'Google Pixel 9 Pro XL', 'Google Pixel 9 Pro', 'Google Pixel 9', 'Google Pixel 8a', 'OnePlus 12 Pro', 'Xiaomi 14 Ultra', 'Xiaomi 14 Pro', 'Xiaomi 14', 'Oppo Find X7 Ultra', 'Vivo X100 Pro', 'Asus ROG Phone 8 Pro', 'Nubia RedMagic 9 Pro', 'Sony Xperia 1 VI', 'Huawei 14 Ultra', 'Realme X90 Pro']), 'Laptop': ('laptop', ['MacBook Pro 16 M4 Max', 'MacBook Pro 14 M4 Pro', 'MacBook Air 15 M3', 'MacBook Air 13 M3', 'Dell XPS 16 OLED', 'Dell XPS 14', 'Dell XPS 13 Plus', 'Dell Alienware m16 R2', 'Asus ROG Zephyrus G14', 'Asus ROG Strix Scar 18', 'Asus Zenbook 14 OLED', 'Asus TUF Gaming A15', 'Lenovo Legion Pro 7i', 'Lenovo ThinkPad X1 Carbon Gen 12', 'Lenovo Yoga 9i', 'Lenovo IdeaPad Pro 5i', 'HP Spectre x360 14', 'HP Omen 16', 'HP Victus 15', 'HP Envy 16', 'MSI Stealth 16 Ultra', 'MSI Raider GE78', 'Razer Blade 16', 'Razer Blade 14', 'Acer Predator Helios 18']), 'Âm thanh': ('headphones speaker', ['Sony WH-1000XM6', 'Sony WF-1000XM5', 'AirPods Pro Gen 3', 'AirPods Max 2', 'Bose QuietComfort Ultra', 'Bose QuietComfort Earbuds 2', 'Sennheiser Momentum 4', 'Sennheiser Accentum', 'Jabra Elite 10', 'Jabra Elite 8 Active', 'Beats Studio Pro', 'Beats Fit Pro', 'Samsung Galaxy Buds 3 Pro', 'Google Pixel Buds Pro 2', 'Marshall Motif II', 'Marshall Major V', 'Bowers & Wilkins Beoplay H95', 'JBL Tour One M2', 'JBL Charge 5', 'JBL Flip 6', 'Sonos Play:5', 'Harmon Kardon Aura Studio 4', 'Devialet Beoplay', 'Audio-Technica True Wireless', 'Anker Soundcore Motion']), 'Thời trang': ('clothing fashion apparel', ['Áo Thun Nam Cotton', 'Áo Sơ Mi Nam Oxford', 'Quần Jean Nam Levi', 'Áo Khoác Denim Chống Nước', 'Áo Polo Thể Thao Nam', 'Váy Liền Nữ Xinh Xắn', 'Đầm Dạ Hội Công Chúa', 'Áo Hoodie Nam Tính', 'Áo Len Nữ Mũ Đỉnh', 'Quần Kaki Nam Cao Cấp', 'Áo Dài Truyền Thống', 'Áo Vest Nam Thanh Lịch', 'Đồ Bộ Ngủ Nữ Lụa', 'Áo Khoác Gió Nữ', 'Quần Short Jean Nữ', 'Áo Phông Oversize Nữ', 'Quần Âu Nam Công Sở', 'Váy Cưới Thanh Lịch', 'Đầm Body Phá Cách', 'Quần baggy Nữ', 'Áo Dạ Nữ Thu Đông', 'Áo Nỉ Nam Mùa Đông', 'Bộ Đồ Thể Thao Nam', 'Set Đồ Tập Yoga Nữ', 'Khăn Quàng Cổ Lụa']), 'Giày dép': ('shoes sneakers', ['Nike Air Max 2026', 'Nike Air Force 1', 'Nike ZoomX Vaporfly', 'Nike Dunk Low', 'Nike Pegasus 40', 'Adidas Ultraboost Light 2', 'Adidas Yeezy Boost 350', 'Adidas NMD R2', 'Adidas Stan Smith', 'Adidas Superstar', 'Puma RS-X', 'Puma Suede Classic', 'Vans Old Skool', 'Vans Authentic', 'Converse Chuck Taylor 70s', 'New Balance 990v6', 'New Balance 550', 'New Balance 2002R', 'Asics Gel-Kayano 30', 'Asics Nimbus 26', 'Reebok Club C 85', 'Balenciaga Triple S', 'Gucci Track Sneakers', 'Salomon XT-6', 'Clarks Desert Boot']), 'Gia dụng': ('home appliance', ['Máy Hút Bụi Dyson V16', 'Robot Hút Bụi Roborock S9', 'Máy Lọc Không Khí LG Puricare', 'Máy Giặt Cửa Trước Samsung AI', 'Tủ Lạnh Bosch 4 Cửa', 'Quạt Không Cánh Dyson Pure Cool', 'Bàn Ủi Hơi Nước Philips', 'Máy Sấy Điện Electrolux', 'Máy Lau Nhà Tự Động Dreame', 'Máy Lọc Nước RO Karofi', 'Tủ Lạnh Side-by-side Panasonic', 'Máy Giặt Sấy Kèm LG', 'Bình Nước Nóng Ariston', 'Quạt Trần Panasonic', 'Đèn Chùm Hiện Đại', 'Máy Sưởi Dầu Tiross', 'Máy Điều Hòa Daikin Inverter', 'Tủ Lạnh LG Instaview', 'Máy Hút Ẩm Sharp', 'Máy Tạo Ẩm Xiaomi', 'Chuông Cửa Màn Hình', 'Khóa Cửa Thông Minh Yale', 'Quạt Cây Mitsubishi', 'Máy Diệt Khuẩn Không Khí', 'Tủ Sấy Quần Áo']), 'Nhà bếp': ('kitchen appliance', ['Nồi Chiên Không Dầu Philips XXL', 'Lò Vi Sóng Panasonic', 'Máy Ép Chậm Hurom', 'Máy Phà Cà Phê Delonghi', 'Máy Xay Sinh Tố Blendtec', 'Bếp Từ Bosch Series 8', 'Nồi Áp Suất Instant Pot Pro', 'Máy Rửa Bát Siemens', 'Máy Nướng Bánh Mì Smeg', 'Máy Pha Cà Phê Viên Nén Nespresso', 'Bếp Ga Rinnai', 'Máy Hút Mùi Electrolux', 'Nồi Cơm Điện Tử Toshiba', 'Máy Làm Sữa Hạt Tefal', 'Cân Tiểu Ly Nhà Bếp', 'Máy Trộn Bột KitchenAid', 'Chảo Chống Dính Tefal', 'Bộ Nồi Inox Fissler', 'Máy Đánh Trứng Bosch', 'Máy Nhồi Bột Bear', 'Lò Nướng Sanaky', 'Máy Xay Thịt Philips', 'Bếp Nướng Điện Lock&Lock', 'Máy Ép Trái Cây Panasonic', 'Bếp Hồng Ngoại Sunhouse']), 'Sách': ('book cover', ['Sách Clean Code by Robert C. Martin', 'Sách Đắc Nhân Tâm bản đặc biệt', 'Sách Nhà Giả Kim', 'Sách Tư Duy Nhanh Và Chậm', 'Sách Sức Mạnh Của Thói Quen', 'Sách Lược Sử Loài Người', 'Sách Hành Trình Về Phương Đông', 'Sách Tội Ác Và Hình Phạt', 'Từ Điển Anh Việt Oxford', 'Tiểu Thuyết Harry Potter', 'Sách Dạy Con Làm Giàu Tập 1', 'Sách Nghệ Thuật Tinh Tế Của Việc Đếch Quan Tâm', 'Sách 7 Thói Quen Của Người Thành Đạt', 'Sách Design Patterns', 'Sách System Design Interview', 'Sách Bí Mật Của May Mắn', 'Sách Đời Ngắn Đừng Ngủ Dài', 'Sách Nguồn Gốc Các Loài', 'Sách 100 Quy Luật Của Sự Thành Công', 'Sách Marketing Căn Bản', 'Tiểu Thuyết Bố Già', 'Sách Khởi Nghiệp Tinh Gọn', 'Sách Thay Đổi Tí Hon Hiệu Quả To Lớn', 'Sách Trí Tuệ Xúc Cảm', 'Sách Lãnh Đạo Bằng Sức Mạnh']), 'Gaming': ('gaming setup console', ['PlayStation 5 Pro', 'Xbox Series X 2TB', 'Nintendo Switch OLED 2', 'Kính VR Meta Quest 3', 'Steam Deck OLED', 'Bàn Phím Cơ Razer Huntsman', 'Chuột Gaming Logitech G Pro X', 'Tai Nghe Gaming HyperX Cloud III', 'Màn Hình Gaming Asus ROG 240Hz', 'Màn Hình Samsung Odyssey G9', 'Ghế Gaming Secretlab Titan', 'Card Màn Hình RTX 5090', 'Card Màn Hình Radeon RX 8900 XTX', 'Vô Lăng Đua Xe Logitech G923', 'Microphone Shure SM7B', 'Webcam Logitech Brio 4K', 'Bàn Phím Cơ Corsair Black', 'Tay Cầm Xbox Elite', 'Tay Cầm DualSense Edge', 'Kính Thực Tế Ảo Apple Vision Pro', 'Bàn Chơi Game Herman Miller', 'Router Gaming Asus ROG', 'SSD Samsung 990 Pro', 'Bảng Điều Khiển Elgato Stream Deck', 'Tai Nghe Gaming SteelSeries']), 'Đồng hồ': ('luxury smartwatch', ['Apple Watch Ultra 3', 'Apple Watch Series 10', 'Samsung Galaxy Watch 7 Pro', 'Garmin Fenix 8', 'Garmin Epix Pro', 'Rolex Submariner', 'Rolex Daytona', 'Omega Speedmaster', 'Omega Seamaster', 'Tag Heuer Carrera', 'Longines HydroConquest', 'Tissot PRX', 'Casio G-Shock Mudmaster', 'Casio Edifice', 'Orient Bambino', 'Citizen Tsuyosa', 'Seiko Prospex Diver', 'Seiko Presage', 'Hublot Big Bang', 'Patek Philippe Nautilus', 'Breitling Chronomat', 'IWC Navitimer', 'Tudor Superocean', 'Garmin Forerunner 965', 'Coros Vertix 2']), 'Thể thao & Fitness': ('fitness sport equipment', ['Xe Đạp Tập Thể Dục Peloton', 'Máy Chạy Bộ KingSport', 'Tạ Đơn Điều Chỉnh Bowflex', 'Thảm Tập Yoga Liforme', 'Súng Massage Theragun Pro', 'Băng Đầu Gối Thể Thao', 'Dây Kháng Lực TRX', 'Con Lăn Quần Tập Bụng', 'Xà Đơn Gắn Cửa Cải Tiến', 'Vợt Cầu Lông Yonex Astrox', 'Quả Bóng Rổ Spalding', 'Giày Đá Bóng Nike Mercurial', 'Quần Áo Chạy Bộ Nam', 'Túi Thể Thao Nike', 'Balo Nước Leo Núi', 'Kính Bơi Speedo', 'Găng Tay Tập Gym', 'Dây Nhảy Có Số Đếm', 'Tạ Bình Vôi Kettlebell', 'Ghế Tập Tạ Đa Năng', 'Cung Phượt Cắm Trại', 'Giày Leo Núi Columbia', 'Ván Trượt Ván Vans', 'Quần Bơi Nam Arena', 'Bóng Bàn Molten']), 'Làm đẹp': ('cosmetics skincare', ['Máy Tạo Kiểu Tóc Dyson Airwrap', 'Kem Dưỡng Ẩm La Mer', 'Serum Phục Hồi Estee Lauder', 'Nước Hoa Hồng SK-II', 'Kem Chống Nắng Anessa', 'Son Môi Tom Ford', 'Son Dưỡng Dior', 'Kem Nền Chanel', 'Phấn Phủ YSL', 'Kẻ Mắt Nước Lancome', 'Nước Tẩy Trang Bioderma', 'Sữa Rửa Mặt CeraVe', 'Dầu Gội Phục Hồi Kerastase', 'Mặt Nạ Giấy Mediheal', 'Tẩy Tế Bào Chết Paula Choice', 'Kem Mắt Kiehls', 'Serum Trị Mụn Ordinary', 'Xịt Khoáng Vichy', 'Phấn Nước Cushion Sulwhasoo', 'Tinh Chất Vitamin C', 'Máy Hút Mụn Halio', 'Máy Rửa Mặt Foreo Luna 4', 'Sữa Tắm Bath & Body Works', 'Lotion Dưỡng Thể Nhạt', "Kem Dưỡng Tay L'Occitane"])}

        self.stdout.write('Bắt đầu sinh 300 sản phẩm với hình ảnh độc lập...')
        
        for category_name, value in categories_data.items():
            cat_keyword, product_names = value
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': f'Danh mục {category_name} chất lượng cao',
                    'image_url': f'https://loremflickr.com/600/600/{urllib.parse.quote(cat_keyword.replace(" ", ","))}?lock=999'
                }
            )
            self.stdout.write(f' -> {category_name}')
            
            for idx, name in enumerate(product_names):
                slug = slugify(name)
                price = _get_price(category_name, idx)
                compare_price = _round_to_thousand(price * Decimal('1.2'))
                stock = random.randint(10, 200)
                rating = Decimal(f"{random.uniform(4.0, 5.0):.2f}")
                num_reviews = random.randint(10, 5000)
                
                # Dynamic image placeholder (pollinations is too slow/rate-limits real browsers for 300 images)
                # Dùng loremflickr có từ khóa category đảm bảo 300 ảnh riêng biệt & liên quan & TRẢ VỀ NGAY LẬP TỨC
                encoded_keyword = urllib.parse.quote(cat_keyword.replace(' ', ','))
                image_url = f"https://loremflickr.com/600/600/{encoded_keyword}?lock={idx}"
                
                Product.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'category': category,
                        'description': f'Phiên bản cao cấp của {name} với chất liệu hoàn thiện và hiệu năng tuyệt vời. Phù hợp cho mọi nhu cầu.',
                        'price': price,
                        'compare_price': compare_price,
                        'stock': stock,
                        'rating': rating,
                        'num_reviews': num_reviews,
                        'image_url': image_url,
                        'is_active': True
                    }
                )
        
        self.stdout.write(self.style.SUCCESS("Đã sinh thành công 300 sản phẩm độc lập!"))
