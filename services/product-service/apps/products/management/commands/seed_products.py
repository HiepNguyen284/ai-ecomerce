import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category, Product


class Command(BaseCommand):
    help = 'Seed 12 categories and 25 products with detailed descriptions for AI consultation'

    def handle(self, *args, **options):
        # ── 12 Categories ──────────────────────────────────────────────
        categories_raw = [
            {
                'name': 'Quần',
                'description': 'Các loại quần nam nữ từ jean, kaki, âu, jogger đến quần short, phù hợp mọi phong cách và dịp sử dụng.',
                'image_url': 'https://picsum.photos/seed/cat_pants/600/600',
            },
            {
                'name': 'Áo',
                'description': 'Đa dạng áo thun, sơ mi, hoodie, khoác và áo len cho nam nữ, chất liệu cao cấp, nhiều mẫu mã thời thượng.',
                'image_url': 'https://picsum.photos/seed/cat_shirt/600/600',
            },
            {
                'name': 'Giầy',
                'description': 'Giầy thể thao, giầy da, sneakers, boots và sandal từ các thương hiệu hàng đầu thế giới.',
                'image_url': 'https://picsum.photos/seed/cat_shoes/600/600',
            },
            {
                'name': 'Laptop',
                'description': 'Laptop văn phòng, gaming, đồ hoạ và ultrabook từ Apple, Dell, Asus, Lenovo với cấu hình mạnh mẽ.',
                'image_url': 'https://picsum.photos/seed/cat_laptop/600/600',
            },
            {
                'name': 'Điện thoại',
                'description': 'Smartphone cao cấp và tầm trung từ Apple, Samsung, Xiaomi với camera, chip xử lý và pin thế hệ mới nhất.',
                'image_url': 'https://picsum.photos/seed/cat_phone/600/600',
            },
            {
                'name': 'Đồng hồ',
                'description': 'Đồng hồ cơ, smartwatch và đồng hồ thời trang từ Rolex, Casio, Apple Watch, Garmin cho mọi phong cách.',
                'image_url': 'https://picsum.photos/seed/cat_watch/600/600',
            },
            {
                'name': 'Ô tô',
                'description': 'Phụ kiện và đồ chơi ô tô cao cấp: camera hành trình, máy lọc không khí, bọc vô lăng, GPS và thiết bị an toàn.',
                'image_url': 'https://picsum.photos/seed/cat_car/600/600',
            },
            {
                'name': 'Sách',
                'description': 'Sách self-help, văn học, kỹ thuật lập trình, kinh doanh và khoa học từ các tác giả nổi tiếng trong và ngoài nước.',
                'image_url': 'https://picsum.photos/seed/cat_book/600/600',
            },
            {
                'name': 'Mỹ phẩm',
                'description': 'Mỹ phẩm chăm sóc da, trang điểm và dưỡng tóc từ các thương hiệu Hàn Quốc, Pháp, Mỹ uy tín hàng đầu.',
                'image_url': 'https://picsum.photos/seed/cat_cosmetics/600/600',
            },
            {
                'name': 'Âm thanh',
                'description': 'Tai nghe, loa bluetooth, soundbar và thiết bị âm thanh hi-fi từ Sony, Bose, JBL, Marshall chất lượng studio.',
                'image_url': 'https://picsum.photos/seed/cat_audio/600/600',
            },
            {
                'name': 'Đồ gia dụng',
                'description': 'Thiết bị gia dụng thông minh: máy hút bụi, máy lọc không khí, nồi chiên không dầu, robot lau nhà tiết kiệm năng lượng.',
                'image_url': 'https://picsum.photos/seed/cat_home/600/600',
            },
            {
                'name': 'Túi xách',
                'description': 'Túi xách nữ, balo nam, cặp laptop và ví da từ các thương hiệu thời trang cao cấp và bình dân.',
                'image_url': 'https://picsum.photos/seed/cat_bag/600/600',
            },
        ]

        cat_map = {}
        for c in categories_raw:
            obj, created = Category.objects.update_or_create(
                name=c['name'],
                defaults={
                    'description': c['description'],
                    'image_url': c['image_url'],
                }
            )
            cat_map[c['name']] = obj
            status = 'TẠO MỚI' if created else 'CẬP NHẬT'
            self.stdout.write(f'  [{status}] Category: {c["name"]}')

        # ── 25 Products ────────────────────────────────────────────────
        products_data = [
            # ─── Quần (2) ───
            {
                'name': 'Quần Jean Nam Levi\'s 511 Slim Fit Xanh Đậm',
                'category': 'Quần',
                'price': Decimal('1890000'),
                'compare_price': Decimal('2490000'),
                'stock': 120,
                'rating': Decimal('4.70'),
                'num_reviews': 1843,
                'image_url': 'https://picsum.photos/seed/levis511_jeans/600/600',
                'description': (
                    "Quần Jean Nam Levi's 511 Slim Fit phiên bản Xanh Đậm (Dark Indigo Wash) là dòng quần bán chạy nhất của Levi's toàn cầu. "
                    "Chất liệu: vải denim cotton 98% pha 2% elastane co giãn 4 chiều, trọng lượng vải 12oz, mềm mại nhưng vẫn giữ form tốt sau nhiều lần giặt. "
                    "Kiểu dáng Slim Fit ôm vừa vặn từ hông xuống đùi, ống quần hơi thu nhỏ ở bắp chân, KHÔNG bó sát như skinny – phù hợp cho nam giới có đùi trung bình đến hơi to (size 28-36). "
                    "Đường may kép chắc chắn, 5 túi truyền thống (2 túi trước, 2 túi sau, 1 túi đồng xu), khoá YKK bền bỉ, nút đồng có logo Levi's dập nổi. "
                    "Chiều dài ống tiêu chuẩn 32 inch (có thể bẻ gấu hoặc lên gấu tuỳ ý). Cạp quần vừa – không quá cao, không quá thấp (mid-rise ~10 inch). "
                    "Phù hợp mặc đi làm văn phòng casual, đi chơi, đi date. Kết hợp tốt với áo thun cổ tròn, áo polo, áo sơ mi, áo khoác bomber hoặc blazer. "
                    "Hướng dẫn giặt: giặt máy nước lạnh, lộn trái, không dùng chất tẩy, phơi trong bóng râm để giữ màu. "
                    "Lưu ý: sản phẩm có thể phai nhẹ 5-10% sau 3-5 lần giặt đầu tiên – đây là đặc tính tự nhiên của denim chất lượng cao."
                ),
            },
            {
                'name': 'Quần Kaki Nam Dockers Alpha Slim Tapered Màu Be',
                'category': 'Quần',
                'price': Decimal('1290000'),
                'compare_price': Decimal('1690000'),
                'stock': 85,
                'rating': Decimal('4.55'),
                'num_reviews': 967,
                'image_url': 'https://picsum.photos/seed/dockers_khaki/600/600',
                'description': (
                    "Quần Kaki Nam Dockers Alpha Slim Tapered màu Be (British Khaki) – lựa chọn hoàn hảo cho phong cách smart casual công sở. "
                    "Chất liệu: vải twill cotton 97% + 3% spandex, công nghệ Smart 360 Flex™ co giãn đa hướng giúp thoải mái khi ngồi, đứng, cúi. "
                    "Bề mặt vải mịn, chống nhăn nhẹ (wrinkle-resistant), ít phải là ủi – tiết kiệm thời gian buổi sáng. "
                    "Form Slim Tapered: ôm vừa ở hông và đùi, thu nhỏ dần từ đầu gối xuống cổ chân, tạo dáng gọn gàng thanh thoát nhưng không bó. "
                    "Cạp trung (mid-rise), có passant thắt lưng 1.5 inch, khoá kéo ẩn và nút bấm chắc chắn. "
                    "4 túi: 2 túi chéo trước sâu 18cm, 2 túi sau có nút bấm giữ an toàn ví/điện thoại. "
                    "Size: 28-36, chiều dài ống 30/32/34 inch. Màu be này dễ phối đồ nhất – hợp với áo trắng, xanh navy, xanh dương nhạt, hồng pastel. "
                    "Lý tưởng cho: đi làm công sở, họp hành, đi ăn nhà hàng, hẹn hò. Giặt máy ở 30°C, có thể sấy nhẹ."
                ),
            },
            # ─── Áo (2) ───
            {
                'name': 'Áo Sơ Mi Nam Oxford Brooks Brothers Regent Fit Trắng',
                'category': 'Áo',
                'price': Decimal('2490000'),
                'compare_price': Decimal('3200000'),
                'stock': 65,
                'rating': Decimal('4.80'),
                'num_reviews': 2104,
                'image_url': 'https://picsum.photos/seed/brooks_oxford/600/600',
                'description': (
                    "Áo Sơ Mi Nam Oxford Brooks Brothers dòng Regent Fit màu trắng tinh khôi – biểu tượng thời trang công sở Mỹ từ năm 1818. "
                    "Chất liệu: vải Oxford 100% cotton Supima® trồng tại Mỹ, sợi dài tự nhiên cho bề mặt mịn màng, bền gấp 2 lần cotton thường. "
                    "Trọng lượng vải 140gsm – đủ dày để không xuyên thấu nhưng vẫn thoáng mát trong thời tiết Việt Nam 30-35°C. "
                    "Cổ áo button-down cổ điển (cổ có nút cố định) – giữ form cổ áo đẹp cả khi không thắt cà vạt, đặc biệt phù hợp phong cách business casual. "
                    "Form Regent Fit: dáng regular hơi ôm nhẹ ở eo, không quá rộng (traditional fit) cũng không quá bó (slim fit) – phù hợp đa số thể hình nam Việt Nam. "
                    "Chi tiết cao cấp: đường may 18-20 mũi/inch (standard là 12), nút áo bằng xà cừ tự nhiên, gia cố tại các điểm chịu lực (nách, cổ, tay). "
                    "Size S-XXL (tương đương 38-46 Việt Nam). Túi ngực trái có logo BB thêu nhỏ tinh tế. "
                    "Mặc được cho: phỏng vấn xin việc, đi làm hàng ngày, đám cưới, tiệc tối. Phối với quần âu, kaki, hoặc jean đều đẹp. "
                    "Giặt máy 40°C, là ủi nhiệt độ trung bình. Sản phẩm giữ trắng tốt sau 50+ lần giặt nếu tuân thủ hướng dẫn."
                ),
            },
            {
                'name': 'Áo Hoodie Unisex Nike Tech Fleece Full-Zip Xám Đen',
                'category': 'Áo',
                'price': Decimal('2890000'),
                'compare_price': Decimal('3590000'),
                'stock': 48,
                'rating': Decimal('4.85'),
                'num_reviews': 3214,
                'image_url': 'https://picsum.photos/seed/nike_techfleece/600/600',
                'description': (
                    "Áo Hoodie Unisex Nike Tech Fleece Full-Zip phiên bản Xám Đen (Dark Heather Grey) – dòng sản phẩm iconic của Nike từ 2013. "
                    "Chất liệu: Nike Tech Fleece™ độc quyền – cấu trúc 3 lớp gồm 2 lớp jersey cotton mềm mịn kẹp 1 lớp foam cách nhiệt siêu nhẹ ở giữa. "
                    "Kết quả: ấm như áo lông cừu nhưng mỏng hơn 40%, nhẹ hơn 30% – chỉ nặng 480g (size M). Cực kỳ phù hợp thời tiết 15-25°C hoặc phòng máy lạnh. "
                    "Thiết kế: mũ trùm (hood) 2 lớp có dây rút, khoá kéo YKK 2 chiều full-zip (kéo từ trên xuống HOẶC từ dưới lên), "
                    "2 túi khoá kéo nghiêng có lót vải nhung chống trầy điện thoại, bo gấu tay và eo co giãn ribbed. "
                    "Logo Nike Swoosh dập nổi tone-on-tone ở ngực trái (không in, không thêu – nên bền màu vĩnh viễn). "
                    "Form: relaxed fit, vai rơi nhẹ (drop shoulder), thân dài vừa phải che hết cạp quần. Mặc cho cả nam và nữ. "
                    "Size XS-XXL. Bảng size theo US: M = ngực 100-106cm, dài thân 70cm, dài tay 65cm. "
                    "Phối đồ: mặc với jogger, quần jean, quần short đều phù hợp. Có thể layering bên ngoài áo thun khi trời se lạnh. "
                    "Giặt lộn trái, nước lạnh, không sấy nóng, phơi bóng râm để giữ cấu trúc foam bên trong."
                ),
            },
            # ─── Giầy (2) ───
            {
                'name': 'Giầy Thể Thao Nike Air Max 97 Silver Bullet',
                'category': 'Giầy',
                'price': Decimal('4290000'),
                'compare_price': Decimal('5190000'),
                'stock': 35,
                'rating': Decimal('4.75'),
                'num_reviews': 4521,
                'image_url': 'https://picsum.photos/seed/nike_airmax97/600/600',
                'description': (
                    "Giầy Thể Thao Nike Air Max 97 phiên bản huyền thoại Silver Bullet (Metallic Silver/Varsity Red) – lấy cảm hứng từ tàu cao tốc Shinkansen Nhật Bản. "
                    "Upper: chất liệu mesh kết hợp da tổng hợp cao cấp với các đường sóng chạy ngang đặc trưng, phản chiếu ánh sáng tạo hiệu ứng metallic bắt mắt. "
                    "Đệm: bộ đệm Air Max full-length (toàn bộ chiều dài bàn chân) – nhìn thấy rõ qua cửa sổ trong suốt ở đế giữa. "
                    "Cảm giác đi: êm ái, đàn hồi tốt, giảm chấn hiệu quả khi đi bộ cả ngày. Tuy nhiên KHÔNG phù hợp để chạy bộ chuyên nghiệp (đây là giầy lifestyle). "
                    "Đế ngoài: cao su Waffle pattern bám tốt trên bề mặt khô và ẩm, bền sau 6-12 tháng sử dụng hàng ngày. Chiều cao đế ~3.5cm. "
                    "Trọng lượng: ~370g/chiếc (size 42). Form giầy: hơi dài và hẹp so với tiêu chuẩn Việt Nam – nên chọn lên 0.5 size nếu bàn chân bạn bè ngang. "
                    "Size: 38-46 (EU). Hệ thống buộc dây truyền thống, lưỡi gà có đệm foam. "
                    "Phù hợp: đi chơi, đi học, streetwear, phối với quần jogger/jean/short. Đối tượng: nam nữ yêu thích sneaker culture, tuổi 18-35. "
                    "Bảo quản: lau bằng khăn ẩm, dùng bàn chải mềm cho vết bẩn cứng đầu, không giặt máy, nhồi giấy khi không sử dụng."
                ),
            },
            {
                'name': 'Giầy Da Oxford Cole Haan OriginalGrand Nâu Bò',
                'category': 'Giầy',
                'price': Decimal('5490000'),
                'compare_price': Decimal('6990000'),
                'stock': 22,
                'rating': Decimal('4.65'),
                'num_reviews': 876,
                'image_url': 'https://picsum.photos/seed/colehaan_oxford/600/600',
                'description': (
                    "Giầy Da Oxford Cole Haan OriginalGrand Wingtip màu Nâu Bò (British Tan) – sự kết hợp hoàn hảo giữa giầy tây cổ điển và công nghệ sneaker hiện đại. "
                    "Upper: da bò thật 100% thuộc thủ công, hoàn thiện burnished (đánh bóng gradient) tạo chiều sâu màu sắc – mũi giầy đậm hơn, thân nhạt hơn. "
                    "Hoa văn wingtip (broguing) đục lỗ trang trí truyền thống, thể hiện sự sang trọng và đẳng cấp của quý ông. "
                    "Đế: công nghệ Grand.OS® độc quyền của Cole Haan – đế giữa EVA siêu nhẹ (nhẹ hơn 40% so với giầy tây truyền thống), "
                    "đế ngoài cao su linh hoạt có rãnh flex grooves giúp bàn chân uốn cong tự nhiên khi bước đi. Trọng lượng chỉ ~290g/chiếc. "
                    "Lót giầy: OrthoLite® êm ái, kháng khuẩn, hút ẩm – có thể đi cả ngày 8-10 tiếng không mỏi chân. "
                    "Form giầy: D width (trung bình), phù hợp bàn chân Việt Nam. Size 39-45 (EU). Nên thử trước hoặc đo chân chính xác. "
                    "Phù hợp: đi làm công sở, hội nghị, đám cưới, sự kiện formal/semi-formal. Phối với suit, quần âu, hoặc chino + blazer. "
                    "Bảo quản: dùng xi đánh giầy cùng màu 1-2 tuần/lần, dùng cây giữ form (shoe tree) khi không mang, tránh mưa trực tiếp."
                ),
            },
            # ─── Laptop (3) ───
            {
                'name': 'MacBook Pro 16 inch M4 Max 48GB RAM 1TB SSD',
                'category': 'Laptop',
                'price': Decimal('89990000'),
                'compare_price': Decimal('96990000'),
                'stock': 15,
                'rating': Decimal('4.95'),
                'num_reviews': 1287,
                'image_url': 'https://picsum.photos/seed/macbook_pro16/600/600',
                'description': (
                    "MacBook Pro 16 inch thế hệ mới nhất trang bị chip Apple M4 Max – con chip mạnh nhất từng được đặt trong một chiếc laptop. "
                    "CPU: 16 nhân (12 hiệu năng + 4 tiết kiệm điện), GPU: 40 nhân, Neural Engine 16 nhân xử lý AI/ML cực nhanh. "
                    "RAM: 48GB unified memory băng thông 546GB/s – đủ để chạy đồng thời Final Cut Pro render video 8K, Xcode build project lớn, và Chrome 50+ tab mà không giật lag. "
                    "SSD: 1TB NVMe, tốc độ đọc 7.4GB/s ghi 6.3GB/s – khởi động macOS trong 8 giây, mở Photoshop file 2GB trong 3 giây. "
                    "Màn hình: Liquid Retina XDR 16.2 inch, mini-LED, 3456×2234px, 254ppi, độ sáng 1000 nits (SDR) / 1600 nits (HDR peak), "
                    "ProMotion 120Hz adaptive, hỗ trợ P3 wide color gamut – chuẩn màu cho designer, photographer, colorist chuyên nghiệp. "
                    "Pin: lên đến 24 giờ xem video, 18 giờ duyệt web – pin laptop tốt nhất thị trường. Sạc MagSafe 140W (0-50% trong 30 phút). "
                    "Cổng kết nối: 3× Thunderbolt 5 (USB-C), 1× HDMI 2.1, 1× SDXC, 1× MagSafe 3, jack 3.5mm. "
                    "Hệ thống 6 loa với Spatial Audio, 3 micro studio-quality. Camera 1080p Center Stage. "
                    "Trọng lượng: 2.14kg. Vỏ nhôm nguyên khối tái chế, màu Space Black. macOS Sequoia. "
                    "Đối tượng: lập trình viên, nhà thiết kế đồ hoạ, editor video chuyên nghiệp, kỹ sư AI/ML, người cần workstation di động."
                ),
            },
            {
                'name': 'Laptop Dell XPS 14 OLED Core Ultra 7 32GB RAM',
                'category': 'Laptop',
                'price': Decimal('42990000'),
                'compare_price': Decimal('48990000'),
                'stock': 28,
                'rating': Decimal('4.60'),
                'num_reviews': 654,
                'image_url': 'https://picsum.photos/seed/dell_xps14/600/600',
                'description': (
                    "Dell XPS 14 OLED (2025) – ultrabook Windows cao cấp nhất với thiết kế không viền InfinityEdge ấn tượng. "
                    "CPU: Intel Core Ultra 7 155H (16 nhân, 22 luồng), tích hợp NPU Intel AI Boost cho các tác vụ AI on-device như Copilot, Stable Diffusion local. "
                    "GPU: Intel Arc tích hợp (đủ mạnh cho Photoshop, Illustrator, video editing 4K) – KHÔNG có GPU rời nên KHÔNG phù hợp cho gaming AAA hoặc render 3D nặng. "
                    "RAM: 32GB LPDDR5X-7467MHz (hàn chết, không nâng cấp được). SSD: 1TB PCIe Gen 4 NVMe. "
                    "Màn hình: 14.5 inch OLED 3.2K (3200×2000), 120Hz, 100% DCI-P3, Delta E<2, 400 nits, HDR 500 – màu sắc sống động, đen tuyệt đối nhờ OLED. "
                    "Bàn phím: hành trình 1.0mm, có đèn nền, touchpad haptic rộng. Bảo mật: vân tay tích hợp nút nguồn, Windows Hello IR camera. "
                    "Pin: 69.5Wh, khoảng 10-12 giờ sử dụng nhẹ (web, office), 5-6 giờ nếu làm việc nặng. Sạc USB-C 65W. "
                    "Cổng: 2× Thunderbolt 4 (USB-C), 1× USB-C 3.2, microSD. Trọng lượng: 1.46kg – dễ dàng bỏ vào balo mang đi. "
                    "Đối tượng: dân văn phòng cao cấp, creative professionals làm 2D, lập trình viên, sinh viên ngành thiết kế cần laptop mỏng nhẹ màn đẹp."
                ),
            },
            {
                'name': 'Laptop Gaming Asus ROG Strix G16 RTX 4070 i9',
                'category': 'Laptop',
                'price': Decimal('52990000'),
                'compare_price': Decimal('59990000'),
                'stock': 18,
                'rating': Decimal('4.70'),
                'num_reviews': 1892,
                'image_url': 'https://picsum.photos/seed/asus_rog_g16/600/600',
                'description': (
                    "Laptop Gaming Asus ROG Strix G16 (2025) – cỗ máy gaming hiệu năng cao với thiết kế đèn LED RGB bắt mắt. "
                    "CPU: Intel Core i9-14900HX (24 nhân, 32 luồng, boost 5.8GHz) – chip laptop mạnh nhất Intel dành cho gaming và streaming. "
                    "GPU: NVIDIA GeForce RTX 4070 Laptop 8GB GDDR6 với TGP 140W – chơi mượt tất cả game AAA 2025 ở 1080p Ultra (Cyberpunk 2077: ~80fps, "
                    "Baldur's Gate 3: ~100fps, CS2: ~300fps). Hỗ trợ DLSS 3.5 Frame Generation, ray tracing, NVIDIA Reflex. "
                    "RAM: 32GB DDR5-5600MHz (2 khe SO-DIMM, nâng cấp tối đa 64GB). SSD: 1TB PCIe Gen 4 (có slot M.2 thứ 2 để mở rộng). "
                    "Màn hình: 16 inch IPS QHD+ (2560×1600), 240Hz refresh rate, 3ms response time, 100% DCI-P3, Dolby Vision, G-Sync – mượt mà tuyệt đối cho FPS. "
                    "Bàn phím: per-key RGB, hành trình 1.7mm, N-key rollover, 4 phím macro chuyên dụng. "
                    "Tản nhiệt: hệ thống ROG Intelligent Cooling với tản hơi buồng kín, 2 quạt Arc Flow, 5 ống dẫn nhiệt, khe thoát khí 4 hướng – duy trì 85°C CPU khi full load. "
                    "Pin: 90Wh (3-4 giờ dùng nhẹ, ~1.5 giờ khi gaming). Sạc 330W. Trọng lượng: 2.5kg. "
                    "Cổng: 1× Thunderbolt 4, 2× USB-A 3.2, 1× USB-C 3.2, HDMI 2.1, RJ45 2.5Gbps, jack 3.5mm. "
                    "Đối tượng: game thủ core, streamer, người cần laptop vừa gaming vừa làm việc đồ hoạ/render video."
                ),
            },
            # ─── Điện thoại (3) ───
            {
                'name': 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
                'category': 'Điện thoại',
                'price': Decimal('34990000'),
                'compare_price': Decimal('38990000'),
                'stock': 50,
                'rating': Decimal('4.90'),
                'num_reviews': 8743,
                'image_url': 'https://picsum.photos/seed/iphone16promax/600/600',
                'description': (
                    "iPhone 16 Pro Max 256GB màu Titan Sa Mạc (Desert Titanium) – flagship cao cấp nhất của Apple năm 2025. "
                    "Chip: A18 Pro, tiến trình 3nm thế hệ 2, CPU 6 nhân (2 hiệu năng + 4 tiết kiệm điện), GPU 6 nhân với ray tracing phần cứng, "
                    "Neural Engine 16 nhân xử lý 35 nghìn tỷ phép tính/giây – nền tảng cho Apple Intelligence (AI tạo sinh, Siri nâng cấp, Writing Tools). "
                    "Màn hình: Super Retina XDR OLED 6.9 inch, 2868×1320px, 460ppi, ProMotion 1-120Hz, Always-On Display, "
                    "Dynamic Island, độ sáng 1000 nits (outdoor) / 2000 nits (HDR peak). Viền bezel mỏng nhất từ trước đến nay (1.2mm). "
                    "Camera: hệ thống 3 camera sau – Main 48MP (f/1.78, sensor Sony IMX903 mới, stabilization thế hệ 2), "
                    "Ultra Wide 48MP (f/2.2, macro), Telephoto 12MP 5x zoom quang (tetraprism). Camera trước 12MP TrueDepth, Cinematic Mode 4K 30fps. "
                    "Quay video: 4K 120fps Dolby Vision, Spatial Video cho Apple Vision Pro, Audio Mix (tách giọng nói khỏi tiếng ồn bằng AI). "
                    "Nút Camera Control: nút cạnh mới cho phép chụp ảnh, zoom, chuyển chế độ bằng cử chỉ vuốt/nhấn – như máy ảnh chuyên nghiệp. "
                    "Pin: 4685mAh, 33 giờ phát video, sạc MagSafe 25W (0-50% trong 26 phút), sạc USB-C 45W. "
                    "Khung: titan Grade 5, mặt sau kính frosted. IP68 (chống nước 6m/30 phút). "
                    "Bộ nhớ: 256GB (không hỗ trợ thẻ nhớ). iOS 18 với Apple Intelligence. eSIM + nano-SIM. "
                    "Đối tượng: người dùng cao cấp, nhiếp ảnh gia mobile, content creator, người thích hệ sinh thái Apple."
                ),
            },
            {
                'name': 'Samsung Galaxy S25 Ultra 512GB Titan Xanh',
                'category': 'Điện thoại',
                'price': Decimal('36990000'),
                'compare_price': Decimal('41990000'),
                'stock': 42,
                'rating': Decimal('4.85'),
                'num_reviews': 6231,
                'image_url': 'https://picsum.photos/seed/galaxy_s25ultra/600/600',
                'description': (
                    "Samsung Galaxy S25 Ultra 512GB Titan Xanh (Titanium Blue) – smartphone Android mạnh nhất với bút S Pen tích hợp. "
                    "Chip: Qualcomm Snapdragon 8 Elite for Galaxy (tuỳ chỉnh riêng cho Samsung), tiến trình 3nm, "
                    "CPU Oryon 8 nhân boost 4.47GHz, GPU Adreno 830 – hiệu năng vượt trội 40% so với thế hệ trước. "
                    "RAM: 16GB LPDDR5X. Bộ nhớ: 512GB UFS 4.0 (tốc độ đọc 4.2GB/s). "
                    "Màn hình: Dynamic AMOLED 2X 6.9 inch, QHD+ (3120×1440), LTPO 1-120Hz, 2600 nits peak, "
                    "Gorilla Armor 2 chống phản chiếu (giảm 75% phản chiếu, dễ nhìn ngoài nắng hơn mọi đối thủ). "
                    "Camera: 200MP (f/1.7, OIS, AI zoom 100x), Ultra Wide 50MP (f/1.9), Telephoto 50MP 5x zoom quang (f/2.6), Telephoto 10MP 3x zoom quang (f/2.4). "
                    "Camera trước 12MP (f/2.2, autofocus). Quay video 8K 30fps, 4K 120fps. "
                    "Galaxy AI: Live Translate (dịch cuộc gọi real-time), Circle to Search, Chat Assist, Note Assist, Photo Assist (xoá vật thể bằng AI). "
                    "S Pen: tích hợp trong thân máy, latency 2.8ms, nhận diện 4096 mức lực nhấn – ghi chú, vẽ, ký tài liệu, điều khiển từ xa camera. "
                    "Pin: 5000mAh, sạc nhanh 45W (0-65% trong 30 phút), sạc không dây 15W, sạc ngược. "
                    "Khung titan, IP68. One UI 7 trên Android 15, cam kết 7 năm cập nhật OS + bảo mật. "
                    "Đối tượng: người dùng Android cao cấp, doanh nhân cần S Pen, nhiếp ảnh gia, power user cần bộ nhớ lớn."
                ),
            },
            {
                'name': 'Xiaomi 14 Ultra 512GB Đen Huyền Bí',
                'category': 'Điện thoại',
                'price': Decimal('23990000'),
                'compare_price': Decimal('27990000'),
                'stock': 30,
                'rating': Decimal('4.72'),
                'num_reviews': 3891,
                'image_url': 'https://picsum.photos/seed/xiaomi14_ultra/600/600',
                'description': (
                    "Xiaomi 14 Ultra 512GB Đen Huyền Bí – flagship chụp ảnh đỉnh cao với ống kính Leica Summilux chính hãng. "
                    "Chip: Qualcomm Snapdragon 8 Gen 3, tiến trình 4nm, CPU 8 nhân Kryo (1× Cortex-X4 3.3GHz), GPU Adreno 750. "
                    "RAM: 16GB LPDDR5X-8533MHz. Bộ nhớ: 512GB UFS 4.0. "
                    "Camera – ĐIỂM MẠNH SỐ 1: hệ thống Leica Summilux gồm 4 camera sau toàn 50MP: "
                    "Main 50MP Sony LYT-900 1 inch (f/1.63-f/4.0 khẩu độ thay đổi vật lý – giống máy ảnh thật, không phải phần mềm), "
                    "Ultra Wide 50MP (f/2.0, 122°), Telephoto 50MP 3.2x (f/2.5), Periscope 50MP 5x (f/2.5). "
                    "Chế độ: Leica Authentic (màu phim kinh điển), Leica Vibrant (màu rực rỡ), Pro mode RAW 14-bit, Street Photography mode. "
                    "Quay video: 8K 24fps, 4K 60fps Dolby Vision, Movie mode với LUTs chuyên nghiệp. "
                    "Màn hình: LTPO AMOLED 6.73 inch, 2K+ (3200×1440), 1-120Hz, 3000 nits peak, Dolby Vision, HDR10+. "
                    "Pin: 5300mAh, sạc nhanh 90W có dây (0-100% trong 33 phút), sạc không dây 50W, sạc ngược 10W. "
                    "Thiết kế: lưng da Eco-Leather (thuần chay) kết hợp kim loại, bền đẹp, chống trơn trượt. IP68. "
                    "Đối tượng: người đam mê nhiếp ảnh di động, fan Leica, content creator cần camera cấp cao với giá rẻ hơn iPhone/Samsung."
                ),
            },
            # ─── Đồng hồ (2) ───
            {
                'name': 'Đồng Hồ Cơ Seiko Presage Cocktail Time SRPK15',
                'category': 'Đồng hồ',
                'price': Decimal('9890000'),
                'compare_price': Decimal('12490000'),
                'stock': 20,
                'rating': Decimal('4.78'),
                'num_reviews': 1456,
                'image_url': 'https://picsum.photos/seed/seiko_presage/600/600',
                'description': (
                    "Đồng Hồ Cơ Seiko Presage Cocktail Time SRPK15 – kiệt tác đồng hồ cơ Nhật Bản lấy cảm hứng từ cocktail Manhattan. "
                    "Bộ máy: Seiko Caliber 4R35 automatic (tự động lên dây cót bằng chuyển động tay), 23 jewels, tần số 21,600 bph (6 nhịp/giây). "
                    "Trữ cót: 41 giờ – đeo liên tục thì không cần lên dây, nghỉ 2 ngày thì cần lắc hoặc lên dây thủ công qua crown. "
                    "Sai số: ±25-30 giây/ngày (bình thường cho đồng hồ cơ tầm giá này, so với quartz ±1 giây/ngày). "
                    "Mặt số: điểm nhấn chính – mặt số radial guilloche pattern màu xanh dương gradient (sẫm ở rìa, nhạt ở tâm), "
                    "tạo hiệu ứng ánh sáng lung linh khi xoay tay giống mặt nước cocktail. Kim và chỉ số giờ dạ quang LumiBrite. "
                    "Vỏ: thép không gỉ 316L đánh bóng, đường kính 40.5mm, dày 11.8mm – kích thước vừa vặn cho cổ tay 16-19cm. "
                    "Mặt kính: Hardlex (thuỷ tinh khoáng cường lực Seiko) – chống trầy tốt hơn kính thường nhưng không bằng sapphire. "
                    "Dây: da bê (calf leather) màu nâu, rộng 20mm, khoá bướm thép. Chống nước: 5ATM (50m) – rửa tay OK, bơi thì không nên. "
                    "Đối tượng: nam giới 25-50 tuổi yêu thích đồng hồ cơ cổ điển, muốn sản phẩm Made in Japan chất lượng ở tầm giá dưới 10 triệu."
                ),
            },
            {
                'name': 'Apple Watch Ultra 2 GPS+Cellular 49mm Titan Tự Nhiên',
                'category': 'Đồng hồ',
                'price': Decimal('21990000'),
                'compare_price': Decimal('23990000'),
                'stock': 25,
                'rating': Decimal('4.88'),
                'num_reviews': 3567,
                'image_url': 'https://picsum.photos/seed/applewatch_ultra2/600/600',
                'description': (
                    "Apple Watch Ultra 2 GPS+Cellular 49mm vỏ Titan Tự Nhiên – đồng hồ thông minh bền bỉ nhất của Apple, thiết kế cho thể thao mạo hiểm. "
                    "Chip: Apple S9 SiP (System in Package) – nhanh hơn 25% so với S8, Neural Engine 4 nhân cho Siri on-device, Double Tap gesture. "
                    "Màn hình: OLED LTPO2 Always-On 1.93 inch (49mm), 502×410px, 3000 nits max (sáng nhất trong tất cả Apple Watch) – đọc rõ dưới nắng gay gắt. "
                    "Vỏ: Titan Grade 5 (aerospace-grade), mặt kính sapphire phẳng chống trầy, viền gờ bảo vệ. Nút Action Button lập trình được (workout, compass waypoint, flashlight...). "
                    "Kết nối: GPS 2 tần số (L1+L5) chính xác đến 1m, cellular eSIM (gọi/nhắn không cần iPhone), Wi-Fi 4, Bluetooth 5.3, UWB chip U2. "
                    "Cảm biến: nhịp tim quang học Gen 4, SpO2, nhiệt độ cổ tay, la bàn, cao độ kế, gia tốc kế 256g (phát hiện tai nạn xe), gyroscope, áp suất khí quyển. "
                    "Chống nước: WR100 + EN13319 (đạt chuẩn lặn 40m), hoạt động ở -20°C đến +55°C. Loa Siren 86dB (kêu cứu khi gặp nạn). "
                    "Pin: 36 giờ (sử dụng bình thường), 72 giờ (chế độ tiết kiệm pin) – đủ chạy ultra-marathon. Sạc từ tính nhanh (80% trong 60 phút). "
                    "Tính năng đặc biệt: Depth app (đo độ sâu lặn), Oceanic+ (nhật ký lặn), Backtrack GPS, Precision Finding cho AirTag. "
                    "Dây đi kèm: Alpine Loop hoặc Trail Loop (tuỳ lựa chọn), rộng 49mm. watchOS 11. "
                    "Đối tượng: vận động viên, người thích leo núi/lặn/chạy trail, hoặc người dùng Apple muốn đồng hồ pin trâu, màn hình to, siêu bền."
                ),
            },
            # ─── Ô tô (2) ───
            {
                'name': 'Camera Hành Trình Viofo A139 Pro 3CH 4K HDR+GPS',
                'category': 'Ô tô',
                'price': Decimal('8990000'),
                'compare_price': Decimal('10490000'),
                'stock': 40,
                'rating': Decimal('4.82'),
                'num_reviews': 2341,
                'image_url': 'https://picsum.photos/seed/viofo_dashcam/600/600',
                'description': (
                    "Camera Hành Trình Viofo A139 Pro 3 Kênh (3CH) – giải pháp ghi hình toàn diện 360° cho ô tô với chất lượng 4K. "
                    "Cấu hình 3 camera: Camera trước 4K (3840×2160) sensor Sony STARVIS 2 IMX678, camera trong cabin 1080p hồng ngoại (nhìn rõ ban đêm), "
                    "camera sau 1080p Sony STARVIS. Tổng cộng ghi hình đồng thời 3 góc – không có điểm mù. "
                    "Chất lượng hình: HDR (High Dynamic Range) xử lý cảnh ngược sáng – nhìn rõ biển số xe đối diện khi trời nắng chói. "
                    "Ban đêm: chế độ Night Vision với Sony STARVIS 2 cho hình ảnh sáng rõ, ít noise ngay cả trên đường không có đèn. "
                    "GPS tích hợp: ghi lại tốc độ, toạ độ, tuyến đường trên bản đồ – bằng chứng quan trọng khi xảy ra tai nạn hoặc tranh chấp. "
                    "Tính năng an toàn: phát hiện va chạm (G-sensor) tự động khoá video, chế độ đỗ xe (parking mode) – phát hiện chuyển động/va chạm khi xe tắt máy. "
                    "Kết nối: Wi-Fi 5GHz truyền video nhanh về điện thoại qua app Viofo, Bluetooth cho điều khiển giọng nói. "
                    "Lưu trữ: hỗ trợ thẻ microSD đến 512GB (ghi vòng lặp, tự xoá file cũ). Kèm nguồn 12-24V đấu nối trực tiếp (hardwire kit). "
                    "Lắp đặt: dán kính trước bằng keo 3M, camera sau dán kính sau. Kích thước nhỏ gọn, ẩn sau gương chiếu hậu. "
                    "Đối tượng: chủ xe ô tô muốn bảo vệ an toàn tối đa, tài xế Grab/taxi, người thường xuyên chạy đường dài, xe gia đình có trẻ nhỏ."
                ),
            },
            {
                'name': 'Máy Lọc Không Khí Ô Tô Xiaomi Car Air Purifier Pro',
                'category': 'Ô tô',
                'price': Decimal('2490000'),
                'compare_price': Decimal('3190000'),
                'stock': 55,
                'rating': Decimal('4.52'),
                'num_reviews': 1789,
                'image_url': 'https://picsum.photos/seed/xiaomi_carpurifier/600/600',
                'description': (
                    "Máy Lọc Không Khí Ô Tô Xiaomi Car Air Purifier Pro – giải pháp không khí sạch cho cabin xe hơi. "
                    "Bộ lọc: HEPA H13 kết hợp than hoạt tính – loại bỏ 99.97% bụi mịn PM2.5, phấn hoa, lông thú cưng, vi khuẩn, và 98% formaldehyde/TVOC từ nội thất xe mới. "
                    "Hiệu suất: CADR (Clean Air Delivery Rate) 70m³/h – làm sạch cabin xe sedan 5 chỗ (khoảng 3m³) trong vòng 3 phút. "
                    "Cảm biến: laser PM2.5 sensor đo nồng độ bụi mịn real-time, hiển thị trên màn hình OLED nhỏ gọn với 3 màu (xanh=tốt, cam=trung bình, đỏ=ô nhiễm). "
                    "Chế độ: Auto (tự điều chỉnh tốc độ theo nồng độ bụi), Manual (3 cấp tốc độ), Sleep (im lặng nhất, chỉ 37dB – như tiếng thì thầm). "
                    "Nguồn điện: cắm USB-C vào cổng sạc xe (5V/2A), dây dài 1.5m. Tiêu thụ: tối đa 6.8W – không ảnh hưởng ắc quy. "
                    "Thiết kế: hình trụ tối giản, nhôm anode hóa màu đen, kích thước 72×72×168mm, trọng lượng 520g. "
                    "Gắn vào cốc giữ nước (cup holder) hoặc đặt trên mặt taplo đều vừa. "
                    "Lõi lọc thay thế: tuổi thọ 6 tháng hoặc 2500km, giá lõi khoảng 350.000đ. App Mi Home theo dõi tuổi thọ lọc. "
                    "Đối tượng: người dị ứng, gia đình có trẻ nhỏ, chủ xe mới (nhiều formaldehyde), tài xế chạy trong thành phố ô nhiễm."
                ),
            },
            # ─── Sách (2) ───
            {
                'name': 'Sách "Clean Code" – Robert C. Martin (Bìa Cứng Tiếng Việt)',
                'category': 'Sách',
                'price': Decimal('389000'),
                'compare_price': Decimal('450000'),
                'stock': 200,
                'rating': Decimal('4.92'),
                'num_reviews': 12450,
                'image_url': 'https://picsum.photos/seed/cleancode_book/600/600',
                'description': (
                    "Sách \"Clean Code: Mã Sạch và Con Đường Trở Thành Lập Trình Viên Giỏi\" – tác giả Robert C. Martin (Uncle Bob), bản dịch tiếng Việt bìa cứng sang trọng. "
                    "Nội dung: cuốn sách kinh điển bậc nhất trong ngành phần mềm, dạy bạn cách viết code dễ đọc, dễ bảo trì, dễ mở rộng. "
                    "Cấu trúc: 17 chương + 3 phụ lục, 464 trang. Phần 1 (chương 1-13): nguyên tắc viết code sạch – cách đặt tên biến/hàm có ý nghĩa, "
                    "viết hàm ngắn gọn (dưới 20 dòng), comment đúng cách, xử lý lỗi, unit test, class design theo SOLID. "
                    "Phần 2 (chương 14-16): case studies – tái cấu trúc (refactoring) code thực tế từ xấu sang đẹp, với giải thích từng bước tại sao thay đổi. "
                    "Phần 3 (phụ lục): danh sách \"code smells\" (mùi code xấu) và heuristics để nhận diện và sửa chúng. "
                    "Ngôn ngữ ví dụ: Java (nhưng nguyên tắc áp dụng được cho MỌI ngôn ngữ: Python, JavaScript, C#, Go...). "
                    "Đối tượng đọc: lập trình viên từ 1+ năm kinh nghiệm trở lên. Người mới học code sẽ thấy khó hiểu một số chương. "
                    "KHÔNG phù hợp nếu bạn chưa biết lập trình – hãy học xong cú pháp cơ bản trước. "
                    "In ấn: giấy Cream 80gsm dễ đọc, bìa cứng mạ vàng, khổ 16×24cm, bookmark ribbon. NXB Dân Trí, dịch giả: Nhóm Techcombank Dev Team. "
                    "Tại sao nên đọc: đây là cuốn sách mà 9/10 senior developer khuyên đọc, và là câu hỏi phỏng vấn phổ biến (\"Bạn đã đọc Clean Code chưa?\")."
                ),
            },
            {
                'name': 'Sách "Đắc Nhân Tâm" – Dale Carnegie (Bản Đặc Biệt 2025)',
                'category': 'Sách',
                'price': Decimal('185000'),
                'compare_price': Decimal('239000'),
                'stock': 350,
                'rating': Decimal('4.88'),
                'num_reviews': 25678,
                'image_url': 'https://picsum.photos/seed/dacnhantam_book/600/600',
                'description': (
                    "Sách \"Đắc Nhân Tâm\" (How to Win Friends and Influence People) – Dale Carnegie, bản đặc biệt kỷ niệm 89 năm xuất bản (1936-2025). "
                    "Nội dung: cuốn sách self-help bán chạy nhất mọi thời đại (45+ triệu bản toàn cầu), dạy nghệ thuật giao tiếp, thuyết phục và xây dựng mối quan hệ. "
                    "Cấu trúc 4 phần, 30 nguyên tắc: Phần 1 – Nghệ thuật ứng xử cơ bản (3 nguyên tắc: không chỉ trích, khen ngợi chân thành, khơi gợi ham muốn). "
                    "Phần 2 – 6 cách gây thiện cảm (mỉm cười, nhớ tên, lắng nghe, nói về sở thích người khác...). "
                    "Phần 3 – 12 cách thuyết phục (tránh tranh cãi, thừa nhận sai lầm, đặt câu hỏi thay vì ra lệnh...). "
                    "Phần 4 – 9 cách thay đổi người khác không gây phản cảm (khen trước khi góp ý, để người khác giữ thể diện...). "
                    "Bản đặc biệt 2025: bổ sung thêm chương \"Đắc Nhân Tâm trong kỷ nguyên số\" – áp dụng nguyên tắc Carnegie cho email, mạng xã hội, họp Zoom, và AI. "
                    "In ấn: bìa cứng da PU màu xanh navy dập chữ vàng, giấy Ivory cao cấp 100gsm, 320 trang, khổ 14.5×20.5cm, hộp carton bảo vệ. "
                    "Dịch giả: Nguyễn Hiến Lê (bản dịch kinh điển, ngôn ngữ trang nhã). NXB Tổng Hợp TP.HCM. "
                    "Đối tượng: tất cả mọi người từ 15 tuổi trở lên – đặc biệt người đi làm, quản lý, sales, giáo viên, sinh viên mới ra trường. "
                    "Lưu ý: đây là bản GỐC, không phải bản rút gọn hay tóm tắt. Có nhiều bản giả/kém chất lượng trên thị trường, hãy kiểm tra tem NXB."
                ),
            },
            # ─── Mỹ phẩm (2) ───
            {
                'name': 'Serum Phục Hồi Da Estée Lauder Advanced Night Repair 50ml',
                'category': 'Mỹ phẩm',
                'price': Decimal('2690000'),
                'compare_price': Decimal('3190000'),
                'stock': 75,
                'rating': Decimal('4.83'),
                'num_reviews': 8934,
                'image_url': 'https://picsum.photos/seed/esteelauder_anr/600/600',
                'description': (
                    "Serum Phục Hồi Da Estée Lauder Advanced Night Repair Synchronized Multi-Recovery Complex 50ml – serum chống lão hoá #1 thế giới 13 năm liên tiếp. "
                    "Công nghệ: Chronolux™ CB độc quyền – đồng bộ hoá đồng hồ sinh học tự nhiên của da, tối ưu hoá quá trình tự phục hồi vào ban đêm. "
                    "Thành phần chính: Hyaluronic Acid (cấp ẩm sâu 72h), Tripeptide-32 (kích thích collagen), Bifida Ferment Lysate (tăng cường hàng rào bảo vệ da), "
                    "chiết xuất nấm Tremella (giữ nước gấp 5 lần HA), Vitamin E + Squalane (chống oxy hoá). "
                    "Kết cấu: dạng tinh chất lỏng nhẹ, thẩm thấu nhanh trong 15 giây, không nhờn, không bết dính, phù hợp cả da dầu. "
                    "Công dụng sau 4 tuần sử dụng (theo nghiên cứu lâm sàng trên 600 phụ nữ): giảm 55% nếp nhăn li ti, da sáng hơn 3 tone, "
                    "lỗ chân lông thu nhỏ 38%, da mềm mịn hơn 97%, hàng rào bảo vệ da khoẻ hơn 82%. "
                    "pH: 6.5 – an toàn cho mọi loại da, kể cả da nhạy cảm. Không chứa paraben, phthalate, sulfate. Đã qua kiểm nghiệm da liễu. "
                    "Cách dùng: sau khi rửa mặt + toner, lấy 2-3 giọt ra lòng bàn tay, ấn nhẹ lên mặt và cổ. Dùng sáng và tối. "
                    "Dung tích: 50ml (dùng được 2-3 tháng). Sản xuất tại Bỉ. Hạn sử dụng: 36 tháng (chưa mở), 12 tháng (đã mở). "
                    "Đối tượng: nữ 25+ tuổi bắt đầu có dấu hiệu lão hoá, da xỉn màu, khô, thiếu sức sống. Cũng phù hợp nam giới chăm sóc da."
                ),
            },
            {
                'name': 'Kem Chống Nắng Anessa Perfect UV Sunscreen Skincare Milk 60ml',
                'category': 'Mỹ phẩm',
                'price': Decimal('590000'),
                'compare_price': Decimal('720000'),
                'stock': 150,
                'rating': Decimal('4.90'),
                'num_reviews': 15670,
                'image_url': 'https://picsum.photos/seed/anessa_sunscreen/600/600',
                'description': (
                    "Kem Chống Nắng Anessa Perfect UV Sunscreen Skincare Milk SPF50+ PA++++ 60ml – kem chống nắng bán chạy #1 Nhật Bản 22 năm liên tiếp. "
                    "Chỉ số bảo vệ: SPF50+ (chống UVB gây cháy nắng), PA++++ (mức cao nhất chống UVA gây lão hoá, nám, đốm nâu). "
                    "Công nghệ độc quyền: Auto Booster Technology – khi tiếp xúc với nhiệt độ cao, mồ hôi, hoặc nước, lớp chống nắng TỰ ĐỘNG tăng cường thay vì trôi đi. "
                    "Kết cấu: sữa chống nắng (milk) siêu nhẹ, lắc đều trước khi dùng, thẩm thấu nhanh, không trắng vệt (no white cast), không nhờn rít. "
                    "Thành phần dưỡng: 50% serum skincare công nghệ mới – Hyaluronic Acid, Collagen, chiết xuất hoa anh đào, Vitamin E. "
                    "Khả năng chống nước: Super Waterproof – chịu được 80 phút bơi liên tục, chịu mồ hôi, chịu ma sát (friction-proof). "
                    "Nhưng vẫn dễ rửa bằng sữa rửa mặt thông thường, KHÔNG cần dùng nước tẩy trang riêng. "
                    "Dùng được cho: mặt và body. Không chứa hương liệu, paraben, alcohol (phiên bản Mild Milk). Tested on sensitive skin. "
                    "Cách dùng: lắc chai 5-6 lần, lấy lượng bằng đồng xu, thoa đều lên da 15 phút trước khi ra nắng. Bôi lại mỗi 2-3 giờ nếu ở ngoài trời. "
                    "Dung tích: 60ml (dùng mặt được 1.5-2 tháng). Sản xuất tại Nhật Bản (Shiseido Group). "
                    "Đối tượng: mọi người cần chống nắng hàng ngày, đặc biệt những ai hay ra ngoài, chơi thể thao, đi biển, da dễ bị nám."
                ),
            },
            # ─── Âm thanh (2) ───
            {
                'name': 'Tai Nghe Sony WH-1000XM5 Chống Ồn Chủ Động Bạc',
                'category': 'Âm thanh',
                'price': Decimal('7490000'),
                'compare_price': Decimal('8490000'),
                'stock': 45,
                'rating': Decimal('4.87'),
                'num_reviews': 7823,
                'image_url': 'https://picsum.photos/seed/sony_wh1000xm5/600/600',
                'description': (
                    "Tai Nghe Sony WH-1000XM5 Wireless Noise Cancelling màu Bạc (Platinum Silver) – vua chống ồn chủ động (ANC) trong phân khúc over-ear. "
                    "Chống ồn: 8 microphone + 2 bộ xử lý (HD Noise Cancelling Processor QN1 + Integrated Processor V1) phân tích và triệt tiêu tiếng ồn. "
                    "Hiệu quả ANC: giảm 95% tiếng ồn môi trường – gần như im lặng hoàn toàn trên máy bay, tàu điện, văn phòng ồn ào. "
                    "Chế độ Ambient Sound: bật mic để nghe thông báo sân bay, nói chuyện mà không cần tháo tai nghe. Auto NC Optimizer tự điều chỉnh theo áp suất khí quyển. "
                    "Driver: 30mm Carbon Fiber Composite diaphragm – âm bass sâu chắc, mid ấm tự nhiên, treble mịn không sắc. "
                    "Codec hỗ trợ: SBC, AAC, LDAC (Hi-Res Audio 990kbps – chất lượng gần CD qua Bluetooth), DSEE Extreme (AI upscale nhạc lossy lên gần Hi-Res). "
                    "Pin: 30 giờ liên tục (ANC bật), sạc nhanh 3 phút = 3 giờ nghe. USB-C. Có thể nghe có dây (jack 3.5mm đi kèm) khi hết pin. "
                    "Tiện ích: Multipoint kết nối 2 thiết bị đồng thời (laptop + điện thoại), Speak-to-Chat (tự tạm dừng nhạc khi bạn nói), "
                    "cảm ứng cạnh tai phải (vuốt lên/xuống chỉnh volume, trước/sau chuyển bài, chạm 2 lần play/pause). "
                    "Thiết kế: nhẹ 250g (nhẹ nhất phân khúc), đệm tai da protein mềm mại, headband silicone mỏng, gập phẳng bỏ case. "
                    "Micro gọi điện: 4 beamforming mic + AI loại tiếng ồn gió – gọi Zoom/Teams rõ ràng ngay cả ngoài quán cafe. "
                    "Đối tượng: người đi máy bay thường xuyên, nhân viên văn phòng open-space, audiophile tầm trung, người cần tai nghe all-in-one tốt nhất."
                ),
            },
            {
                'name': 'Loa Bluetooth Marshall Stanmore III Đen Cổ Điển',
                'category': 'Âm thanh',
                'price': Decimal('9990000'),
                'compare_price': Decimal('11490000'),
                'stock': 30,
                'rating': Decimal('4.76'),
                'num_reviews': 3456,
                'image_url': 'https://picsum.photos/seed/marshall_stanmore3/600/600',
                'description': (
                    "Loa Bluetooth Marshall Stanmore III màu Đen Cổ Điển (Classic Black) – loa để bàn hi-fi phong cách vintage rock 'n' roll. "
                    "Driver: hệ thống 3 đường tiếng – 1 tweeter 19mm dome (treble), 1 mid-range 51mm, 1 woofer 133mm (bass). Công suất tổng: 80W RMS. "
                    "Âm thanh: chữ ký âm thanh Marshall đặc trưng – bass đầm ấm sâu, mid dày đặc phù hợp rock/blues/pop, treble sáng nhưng không chói. "
                    "Phòng nghe lý tưởng: 15-40m² – đủ lấp đầy phòng khách với âm lượng lớn không méo ở 80% volume. "
                    "Điều chỉnh: 3 núm vặn analog trên mặt trước (Volume, Treble, Bass) – xoay bằng tay, cảm giác cơ học đã tay, kiểm soát chính xác hơn app. "
                    "Kết nối: Bluetooth 5.2 (SBC, aptX™ Adaptive), RCA 3.5mm AUX, HDMI eARC (kết nối TV làm soundbar). "
                    "Tính năng: Spotify Connect (phát nhạc trực tiếp từ Spotify không cần Bluetooth), Dynamic Loudness (tự cân bằng bass/treble ở volume nhỏ). "
                    "App Marshall Bluetooth: EQ tuỳ chỉnh, bật/tắt Loudness, cập nhật firmware, đặt lịch bật/tắt (Standby Timer). "
                    "Thiết kế: vỏ bọc da vinyl textured đen, lưới loa dệt kim loại, logo Marshall script vàng, viền đồng brass. "
                    "Kích thước: 350×195×185mm, nặng 4.85kg – đặt trên kệ sách, bàn TV, bàn làm việc. Nguồn AC (không có pin – đây là loa để bàn). "
                    "Đối tượng: người yêu nhạc muốn loa để bàn chất lượng cao, fan thương hiệu Marshall, người thích phong cách vintage/retro, "
                    "hoặc cần loa kết nối TV qua HDMI eARC thay soundbar."
                ),
            },
            # ─── Đồ gia dụng (2) ───
            {
                'name': 'Robot Hút Bụi Lau Nhà Roborock S8 MaxV Ultra',
                'category': 'Đồ gia dụng',
                'price': Decimal('28990000'),
                'compare_price': Decimal('33990000'),
                'stock': 20,
                'rating': Decimal('4.91'),
                'num_reviews': 4567,
                'image_url': 'https://picsum.photos/seed/roborock_s8maxv/600/600',
                'description': (
                    "Robot Hút Bụi Lau Nhà Roborock S8 MaxV Ultra – robot dọn nhà thông minh nhất 2025 với dock tự động all-in-one. "
                    "Lực hút: 10,000Pa (mạnh nhất thị trường) – hút sạch bụi mịn, lông thú cưng, mảnh vụn trên sàn gạch, sàn gỗ, thảm dày. "
                    "Hệ thống lau: VibraRise 3.0 – 2 pad lau xoay rung 4000 lần/phút + áp lực xuống sàn 6N, lau sạch vết bẩn cứng đầu (vết café, nước sốt). "
                    "Khi gặp thảm: pad lau TỰ ĐỘNG nâng lên 20mm + tăng lực hút – vừa hút thảm mạnh vừa không làm ướt thảm. "
                    "Camera AI: ReactiveAI 2.0 với camera RGB + đèn LED hồng ngoại – nhận diện và tránh 70+ loại vật thể (giày dép, dây cáp, phân thú cưng, đồ chơi trẻ em) "
                    "ngay cả trong bóng tối hoàn toàn. "
                    "Dock tự động (Ultra): tự xả rác vào túi túi 2.5L (thay túi mỗi 7 tuần), tự giặt pad lau bằng nước nóng 60°C, "
                    "tự sấy khô pad bằng không khí nóng (chống mốc), tự bơm nước sạch + xả nước bẩn – HOÀN TOÀN không cần can thiệp trong 7 tuần. "
                    "Lidar navigation: LDS + 3D ToF chính xác đến mm, lên bản đồ 3D nhiều tầng (biệt thự nhiều tầng), "
                    "chia phòng thông minh, đặt lịch dọn theo phòng, vùng cấm ảo. "
                    "App Roborock: điều khiển từ xa, xem camera real-time (khi đi vắng), tương thích Alexa/Google Home/Siri Shortcuts. "
                    "Pin: 5200mAh, dọn liên tục 180 phút (nhà 200m² một lần sạc), tự về dock sạc rồi tiếp tục dọn. "
                    "Đối tượng: gia đình có thú cưng, nhà rộng 80-200m², người bận rộn muốn tự động hoá việc dọn nhà, người dị ứng bụi."
                ),
            },
            {
                'name': 'Nồi Chiên Không Dầu Philips Airfryer XXL HD9860 7.3L',
                'category': 'Đồ gia dụng',
                'price': Decimal('6490000'),
                'compare_price': Decimal('7990000'),
                'stock': 60,
                'rating': Decimal('4.74'),
                'num_reviews': 5678,
                'image_url': 'https://picsum.photos/seed/philips_airfryer/600/600',
                'description': (
                    "Nồi Chiên Không Dầu Philips Airfryer XXL Connected HD9860 dung tích 7.3L – nồi chiên không dầu cao cấp nhất của Philips. "
                    "Dung tích: 7.3L (lớn nhất dòng Philips) – chiên được nguyên con gà 1.5kg, 1.4kg khoai tây, hoặc pizza 26cm. Phục vụ 4-6 người/lần. "
                    "Công nghệ: Rapid Air với thiết kế starfish (hình sao biển) tạo luồng không khí xoáy 360° đều khắp – thực phẩm giòn ngoài, mềm trong, "
                    "giảm 90% lượng dầu mỡ so với chiên ngập dầu truyền thống. "
                    "Công suất: 2225W – đạt nhiệt 200°C chỉ trong 3 phút (nhanh hơn lò nướng thông thường 10 phút). "
                    "Smart Sensing: cảm biến nhiệt độ thông minh tự điều chỉnh nhiệt + thời gian theo loại thực phẩm và khối lượng – không cần đoán, không lo cháy. "
                    "Chế độ nấu: Chiên giòn, Nướng (grill), Sấy khô (dehydrate 40°C), Hâm nóng, Giữ ấm. Nhiệt độ: 40-200°C. "
                    "Điều khiển: màn hình cảm ứng LED + kết nối Wi-Fi qua app NutriU (700+ công thức nấu, hẹn giờ từ xa, nhận thông báo khi xong). "
                    "Khay chiên: lớp phủ chống dính QuickClean – rửa tay hoặc cho vào máy rửa bát đều được. Thiết kế tháo rời dễ vệ sinh. "
                    "Kích thước: 315×321×404mm, nặng 8.2kg. Màu đen bóng cao cấp. Dây nguồn 1m. "
                    "An toàn: tự ngắt khi mở xoong, tay cầm cách nhiệt, chân đế chống trượt, chứng nhận CE/GS. "
                    "Đối tượng: gia đình 4-6 người, người ăn kiêng/giảm cân muốn ăn giòn ít dầu, người bận rộn cần nấu nhanh, bếp nhỏ không có lò nướng lớn."
                ),
            },
            # ─── Túi xách (3) ───
            {
                'name': 'Balo Laptop Tomtoc Navigator-T71 15.6" Chống Nước Xám',
                'category': 'Túi xách',
                'price': Decimal('1690000'),
                'compare_price': Decimal('2090000'),
                'stock': 90,
                'rating': Decimal('4.68'),
                'num_reviews': 3245,
                'image_url': 'https://picsum.photos/seed/tomtoc_backpack/600/600',
                'description': (
                    "Balo Laptop Tomtoc Navigator-T71 15.6 inch Chống Nước màu Xám Đậm (Space Gray) – balo công nghệ thiết kế tại San Francisco. "
                    "Ngăn laptop: lót nệm 360° CornerArmor™ bảo vệ 4 góc laptop khỏi va đập (đã test rơi từ 1.2m), vừa laptop đến 15.6 inch + tablet 12.9 inch riêng biệt. "
                    "Dung tích: 25L – đủ cho 1 ngày làm việc + tập gym: laptop, sạc, chuột, sổ A4, bình nước 750ml, quần áo thay, ô dù. "
                    "Chất liệu: vải Cordura® ballistic nylon 900D chống mài mòn (bền gấp 3 lần nylon thường), phủ DWR chống nước cấp 4 (mưa nhỏ-vừa 30 phút không thấm). "
                    "Khoá kéo: YKK chống nước, kéo mượt, bền 10,000+ lần kéo. Tay kéo kim loại dễ cầm khi đeo găng tay. "
                    "Hệ thống ngăn: 1 ngăn chính rộng, 1 ngăn phụ phía trước (organizer: ngăn bút, thẻ, passport, chìa khoá, cáp sạc), "
                    "1 túi nhanh trên cùng (đựng AirPods, ví), 2 túi bên (bình nước), 1 túi ẩn lưng (đựng hộ chiếu/tiền chống trộm). "
                    "Thoải mái đeo: lưng đệm Airdex™ thoáng khí 3D, quai vai đệm dày 25mm có dây đai ngực, tay xách trên và bên hông. "
                    "Kích thước: 47×32×18cm, nặng 1.05kg (nhẹ cho balo 25L). Có dải phản quang an toàn ban đêm. Cổng sạc USB bên ngoài. "
                    "Đối tượng: dân văn phòng đi làm hàng ngày, sinh viên, lập trình viên mang laptop thường xuyên, du lịch ngắn ngày 1-2 ngày."
                ),
            },
            {
                'name': 'Túi Xách Nữ Charles & Keith Sculptural Knot Kem',
                'category': 'Túi xách',
                'price': Decimal('1890000'),
                'compare_price': Decimal('2290000'),
                'stock': 45,
                'rating': Decimal('4.62'),
                'num_reviews': 2890,
                'image_url': 'https://picsum.photos/seed/charleskeith_bag/600/600',
                'description': (
                    "Túi Xách Nữ Charles & Keith Sculptural Knot Handle Bag màu Kem (Chalk) – thiết kế sang trọng tối giản từ Singapore. "
                    "Thiết kế: dáng túi structured (giữ form cứng cáp), tay cầm sculptural knot (thắt nút điêu khắc) là chi tiết signature thương hiệu – "
                    "nổi bật, nghệ thuật, là điểm nhấn trang phục. Nắp đậy nam châm ẩn. "
                    "Chất liệu: da tổng hợp cao cấp PU Polyurethane, bề mặt nhẹ vân (saffiano-like), chống trầy nhẹ, dễ lau khi dính bẩn. "
                    "KHÔNG phải da thật – phù hợp người theo chủ nghĩa thuần chay (vegan leather). Lót trong bằng vải polyester đen, dễ vệ sinh. "
                    "Kích thước: 25×19×10cm (W×H×D) – vừa đủ chứa ví dài, điện thoại đến 6.7 inch, son, chìa khoá, khăn giấy, kính mát. "
                    "KHÔNG vừa laptop hay iPad – đây là túi đi chơi/đi event, không phải túi đi làm. "
                    "Ngăn trong: 1 ngăn chính rộng, 1 túi zip nhỏ bên trong, 1 túi hở đựng điện thoại. "
                    "Dây đeo: 2 kiểu – tay cầm ngắn (xách tay) + dây đeo chéo dài tháo rời 110cm (đeo vai hoặc chéo crossbody). "
                    "Màu Kem Chalk này dễ phối: hợp với váy trắng, đầm pastel, blazer đen, jean + áo trắng, outfit công sở và dự tiệc. "
                    "Bảo quản: tránh tiếp xúc nước, lau bằng khăn ẩm, nhồi giấy khi không dùng, bảo quản trong túi vải chống bụi đi kèm. "
                    "Đối tượng: phụ nữ 20-40 tuổi, thích phong cách thanh lịch tối giản, đi ăn tối, đi event, tặng quà sinh nhật bạn gái."
                ),
            },
            {
                'name': 'Ví Da Nam Montblanc Meisterstück Bifold 6cc Đen',
                'category': 'Túi xách',
                'price': Decimal('8990000'),
                'compare_price': Decimal('10500000'),
                'stock': 15,
                'rating': Decimal('4.93'),
                'num_reviews': 1234,
                'image_url': 'https://picsum.photos/seed/montblanc_wallet/600/600',
                'description': (
                    "Ví Da Nam Montblanc Meisterstück Bifold 6 Khe Thẻ (6cc) màu Đen – biểu tượng xa xỉ Đức dành cho quý ông thành đạt. "
                    "Chất liệu: da bê Âu Châu (European calf leather) thuộc thủ công full-grain, nhuộm xuyên suốt (không chỉ phủ bề mặt) – "
                    "khi trầy nhẹ chỉ cần xoa bằng tay là mờ đi, càng dùng da càng bóng đẹp tự nhiên (patina). "
                    "Lót trong: vải jacquard dệt logo Montblanc, chống rách, chống xù lông. "
                    "Thiết kế Bifold (gập đôi): 6 khe thẻ credit card, 2 ngăn thẻ phụ ẩn, 2 ngăn tiền lớn (vừa tiền Việt Nam 500K không cần gập), "
                    "1 ngăn trong suốt đựng CMND/bằng lái. Tổng cộng chứa được 8-10 thẻ + tiền mặt thoải mái. "
                    "Kích thước gập: 11.5×9.5cm, dày 2cm (khi đựng thẻ + tiền) – vừa túi quần sau. Trọng lượng: 80g. "
                    "Chi tiết: logo Montblanc Star hình ngôi sao trắng dập nổi ở mặt trước (kín đáo, không phô trương), "
                    "đường chỉ may Montblanc Navy Blue (chỉ xanh navy đặc trưng), góc bo tròn tinh tế. "
                    "Đóng gói: hộp Montblanc xanh navy sang trọng + túi vải chống bụi + sách hướng dẫn bảo hành + thẻ chứng nhận chính hãng. "
                    "Bảo hành: 2 năm quốc tế (lỗi sản xuất). Bảo quản: tránh nước, tránh ánh nắng trực tiếp, dùng kem dưỡng da 6 tháng/lần. "
                    "Đối tượng: doanh nhân, quản lý, người tìm quà tặng cao cấp (8/3, Valentine, sinh nhật sếp/bố), người sưu tập đồ da luxury. "
                    "Lưu ý: Montblanc có nhiều hàng super fake – chỉ mua tại boutique chính hãng hoặc đại lý uỷ quyền. Kiểm tra serial number trên web Montblanc."
                ),
            },
        ]

        created_count = 0
        updated_count = 0

        for p in products_data:
            cat = cat_map[p['category']]
            slug = slugify(p['name'])
            # Ensure slug isn't too long
            if len(slug) > 250:
                slug = slug[:250]

            _, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': p['name'],
                    'category': cat,
                    'description': p['description'],
                    'price': p['price'],
                    'compare_price': p['compare_price'],
                    'stock': p['stock'],
                    'rating': p['rating'],
                    'num_reviews': p['num_reviews'],
                    'image_url': p['image_url'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(f'  {"✓" if created else "↻"} {p["name"]}')

        # Clean up old products not in the new dataset
        new_slugs = [slugify(p['name'])[:250] for p in products_data]
        old_products = Product.objects.exclude(slug__in=new_slugs)
        old_count = old_products.count()
        old_products.delete()

        # Clean up old categories not in the new dataset
        new_cat_names = [c['name'] for c in categories_raw]
        old_cats = Category.objects.exclude(name__in=new_cat_names)
        old_cat_count = old_cats.count()
        old_cats.delete()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Hoàn tất! Tạo mới: {created_count}, Cập nhật: {updated_count}, '
            f'Xoá sản phẩm cũ: {old_count}, Xoá danh mục cũ: {old_cat_count}'
        ))
        self.stdout.write(self.style.SUCCESS(f'Tổng: {len(products_data)} sản phẩm / {len(categories_raw)} danh mục'))
