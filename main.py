# -*- coding: utf-8 -*-
"""
CHƯƠNG TRÌNH QUẢN LÝ HIỆU THUỐC BẰNG PYTHON
Đề tài số 17 - Học phần Lập trình Python - Trường Đại học Đại Nam

Dữ liệu được lưu bằng tệp TXT:
    medicines.txt : mỗi dòng là một loại thuốc, các trường cách nhau bởi dấu "|"
    sales.txt     : mỗi dòng là một giao dịch bán thuốc, các trường cách nhau bởi dấu "|"
"""

from datetime import datetime, date

# ---------------------------------------------------------------------------
# HẰNG SỐ CẤU HÌNH
# ---------------------------------------------------------------------------
MEDICINE_FILE = "medicines.txt"
SALES_FILE = "sales.txt"
SEPARATOR = "|"
DATE_FORMAT = "%d/%m/%Y"
LOW_STOCK_THRESHOLD = 5      # thuốc có tồn kho <= ngưỡng này được coi là sắp hết
NEAR_EXPIRY_DAYS = 30        # cảnh báo thuốc hết hạn trong vòng 30 ngày tới

LINE = "=" * 40


# ---------------------------------------------------------------------------
# HÀM TIỆN ÍCH: NHẬP VÀ KIỂM TRA DỮ LIỆU
# ---------------------------------------------------------------------------
def read_text(prompt, allow_empty=False):
    """Nhập chuỗi; không cho phép rỗng và không chứa ký tự phân cách '|'."""
    while True:
        value = input(prompt).strip()
        if SEPARATOR in value:
            print(f"Lỗi: không được dùng ký tự '{SEPARATOR}' trong dữ liệu.")
            continue
        if value == "" and not allow_empty:
            print("Lỗi: không được để trống.")
            continue
        return value


def read_float(prompt, minimum=0.0, allow_equal=False, allow_empty=False):
    """Nhập số thực lớn hơn (hoặc bằng) giá trị tối thiểu."""
    while True:
        text = input(prompt).strip()
        if text == "" and allow_empty:
            return None
        try:
            value = float(text)
        except ValueError:
            print("Lỗi: vui lòng nhập một số hợp lệ.")
            continue
        if value < minimum or (value == minimum and not allow_equal):
            print("Lỗi: giá trị không hợp lệ.")
            continue
        return value


def read_int(prompt, minimum=0, allow_empty=False):
    """Nhập số nguyên lớn hơn hoặc bằng giá trị tối thiểu."""
    while True:
        text = input(prompt).strip()
        if text == "" and allow_empty:
            return None
        try:
            value = int(text)
        except ValueError:
            print("Lỗi: vui lòng nhập một số nguyên hợp lệ.")
            continue
        if value < minimum:
            print(f"Lỗi: giá trị phải lớn hơn hoặc bằng {minimum}.")
            continue
        return value


def parse_date(text):
    """Chuyển chuỗi DD/MM/YYYY thành kiểu date; ném ValueError nếu sai định dạng."""
    return datetime.strptime(text, DATE_FORMAT).date()


def read_date(prompt, allow_empty=False):
    """Nhập hạn sử dụng theo định dạng DD/MM/YYYY."""
    while True:
        text = input(prompt).strip()
        if text == "" and allow_empty:
            return None
        try:
            parse_date(text)
        except ValueError:
            print("Lỗi: ngày không hợp lệ, vui lòng nhập theo dạng DD/MM/YYYY.")
            continue
        return text


def confirm(prompt):
    """Hỏi xác nhận có/không."""
    return input(prompt).strip().lower() in ("y", "yes", "c", "co", "có")


def money(value):
    """Định dạng tiền: 35000 -> 35,000"""
    return f"{value:,.0f}"


# ---------------------------------------------------------------------------
# HÀM NGHIỆP VỤ CƠ BẢN
# ---------------------------------------------------------------------------
def is_expired(date_text):
    """Trả về True nếu hạn sử dụng đã qua ngày hiện tại."""
    return parse_date(date_text) < date.today()


def days_to_expiry(date_text):
    """Số ngày còn lại đến hạn sử dụng (âm nếu đã hết hạn)."""
    return (parse_date(date_text) - date.today()).days


def find_medicine(medicines, code):
    """Tìm thuốc theo mã (không phân biệt hoa/thường). Trả về dictionary hoặc None."""
    for m in medicines:
        if m["ma_thuoc"].lower() == code.strip().lower():
            return m
    return None


def calculate_total(price, quantity):
    """Thành tiền = đơn giá x số lượng."""
    return price * quantity


# ---------------------------------------------------------------------------
# HIỂN THỊ
# ---------------------------------------------------------------------------
def display_medicines(medicines, title="DANH SÁCH THUỐC"):
    """In danh sách thuốc dạng bảng."""
    print(f"\n--- {title} ---")
    if not medicines:
        print("Danh sách thuốc hiện đang rỗng.")
        return
    header = (f"{'Mã':<6}{'Tên thuốc':<23}{'Loại':<18}{'ĐVT':<6}"
              f"{'Đơn giá':>9}{'Tồn':>5}  {'HSD':<12}{'Nhà cung cấp':<16}")
    print(header)
    print("-" * len(header))
    has_expired = False
    for m in medicines:
        expired = is_expired(m["han_su_dung"])
        has_expired = has_expired or expired
        hsd = m["han_su_dung"] + ("*" if expired else "")
        print(f"{m['ma_thuoc']:<6}{m['ten_thuoc'][:22]:<23}{m['loai_thuoc'][:17]:<18}"
              f"{m['don_vi_tinh'][:5]:<6}{money(m['don_gia']):>9}{m['so_luong_ton']:>5}  "
              f"{hsd:<12}{m['nha_cung_cap'][:15]:<16}")
    print(f"Tổng cộng: {len(medicines)} loại thuốc.")
    if has_expired:
        print("(*) Thuốc đã hết hạn sử dụng, không được phép bán.")


# ---------------------------------------------------------------------------
# QUẢN LÝ THUỐC: THÊM - SỬA - XÓA
# ---------------------------------------------------------------------------
def input_medicine(medicines):
    """Nhập thông tin một loại thuốc mới (kiểm tra mã trùng và dữ liệu hợp lệ)."""
    while True:
        code = read_text("Mã thuốc: ")
        if find_medicine(medicines, code):
            print("Lỗi: mã thuốc đã tồn tại, vui lòng nhập mã khác.")
        else:
            break
    return {
        "ma_thuoc": code.upper(),
        "ten_thuoc": read_text("Tên thuốc: "),
        "loai_thuoc": read_text("Loại thuốc: "),
        "don_vi_tinh": read_text("Đơn vị tính: "),
        "don_gia": read_float("Đơn giá (VNĐ): ", minimum=0),
        "so_luong_ton": read_int("Số lượng tồn: ", minimum=0),
        "han_su_dung": read_date("Hạn sử dụng (DD/MM/YYYY): "),
        "nha_cung_cap": read_text("Nhà cung cấp: "),
        "so_luong_da_ban": 0,
    }


def add_medicine(medicines):
    """Thêm một loại thuốc mới vào danh sách."""
    print("\n--- THÊM THUỐC MỚI ---")
    medicines.append(input_medicine(medicines))
    print("Thêm thuốc thành công.")


def update_medicine(medicines):
    """Cập nhật thông tin thuốc; nhấn Enter để giữ nguyên giá trị cũ."""
    print("\n--- CẬP NHẬT THÔNG TIN THUỐC ---")
    code = read_text("Nhập mã thuốc cần cập nhật: ")
    medicine = find_medicine(medicines, code)
    if medicine is None:
        print("Thuốc không tồn tại.")
        return
    print("Nhấn Enter để giữ nguyên giá trị hiện tại.")

    while True:
        new_code = read_text(f"Mã thuốc [{medicine['ma_thuoc']}]: ", allow_empty=True)
        other = find_medicine(medicines, new_code) if new_code else None
        if other is not None and other is not medicine:
            print("Lỗi: mã thuốc đã tồn tại ở thuốc khác.")
            continue
        break
    if new_code:
        medicine["ma_thuoc"] = new_code.upper()

    for field, label in (("ten_thuoc", "Tên thuốc"), ("loai_thuoc", "Loại thuốc"),
                         ("don_vi_tinh", "Đơn vị tính"), ("nha_cung_cap", "Nhà cung cấp")):
        value = read_text(f"{label} [{medicine[field]}]: ", allow_empty=True)
        if value:
            medicine[field] = value

    price = read_float(f"Đơn giá [{money(medicine['don_gia'])}]: ", minimum=0, allow_empty=True)
    if price is not None:
        medicine["don_gia"] = price
    stock = read_int(f"Số lượng tồn [{medicine['so_luong_ton']}]: ", minimum=0, allow_empty=True)
    if stock is not None:
        medicine["so_luong_ton"] = stock
    expiry = read_date(f"Hạn sử dụng [{medicine['han_su_dung']}]: ", allow_empty=True)
    if expiry:
        medicine["han_su_dung"] = expiry
    print("Cập nhật thông tin thuốc thành công.")


def delete_medicine(medicines):
    """Xóa thuốc theo mã sau khi người dùng xác nhận."""
    print("\n--- XÓA THUỐC ---")
    code = read_text("Nhập mã thuốc cần xóa: ")
    medicine = find_medicine(medicines, code)
    if medicine is None:
        print("Thuốc không tồn tại.")
        return
    if confirm(f"Xác nhận xóa '{medicine['ten_thuoc']}' (y/n)? "):
        medicines.remove(medicine)
        print("Đã xóa thuốc.")
    else:
        print("Đã hủy thao tác xóa.")


# ---------------------------------------------------------------------------
# TÌM KIẾM VÀ SẮP XẾP
# ---------------------------------------------------------------------------
SEARCH_FIELDS = {"1": "ma_thuoc", "2": "ten_thuoc", "3": "loai_thuoc", "4": "nha_cung_cap"}


def search_medicines(medicines):
    """Tìm thuốc theo mã, tên, loại hoặc nhà cung cấp (khớp một phần, không phân biệt hoa/thường)."""
    print("\n--- TÌM KIẾM THUỐC ---")
    print("1. Mã thuốc\n2. Tên thuốc\n3. Loại thuốc\n4. Nhà cung cấp")
    choice = input("Chọn tiêu chí tìm kiếm: ").strip()
    if choice not in SEARCH_FIELDS:
        print("Lựa chọn không hợp lệ.")
        return
    keyword = read_text("Nhập từ khóa: ").lower()
    field = SEARCH_FIELDS[choice]
    results = [m for m in medicines if keyword in m[field].lower()]
    if results:
        display_medicines(results, "KẾT QUẢ TÌM KIẾM")
    else:
        print("Không tìm thấy thuốc phù hợp.")


SORT_FIELDS = {"1": "ten_thuoc", "2": "don_gia", "3": "so_luong_ton"}


def sort_medicines(medicines, field, descending=False):
    """Trả về danh sách mới đã sắp xếp theo trường field."""
    if field == "ten_thuoc":
        return sorted(medicines, key=lambda m: m[field].lower(), reverse=descending)
    return sorted(medicines, key=lambda m: m[field], reverse=descending)


def sort_menu(medicines):
    """Cho người dùng chọn tiêu chí và chiều sắp xếp rồi hiển thị kết quả."""
    print("\n--- SẮP XẾP DANH SÁCH THUỐC ---")
    print("1. Theo tên thuốc\n2. Theo đơn giá\n3. Theo số lượng tồn")
    choice = input("Chọn tiêu chí sắp xếp: ").strip()
    if choice not in SORT_FIELDS:
        print("Lựa chọn không hợp lệ.")
        return
    order = input("Chọn chiều sắp xếp (1. Tăng dần, 2. Giảm dần): ").strip()
    if order not in ("1", "2"):
        print("Lựa chọn không hợp lệ.")
        return
    result = sort_medicines(medicines, SORT_FIELDS[choice], descending=(order == "2"))
    display_medicines(result, "DANH SÁCH SAU KHI SẮP XẾP")


# ---------------------------------------------------------------------------
# BÁN THUỐC
# ---------------------------------------------------------------------------
def sell_medicine(medicines, sales):
    """Bán thuốc: nhập nhiều mặt hàng, kiểm tra hạn/tồn kho, lập hóa đơn, cập nhật kho."""
    print("\n--- BÁN THUỐC VÀ LẬP HÓA ĐƠN ---")
    cart = []   # mỗi phần tử: {"medicine": dict, "so_luong": int}
    while True:
        code = input("Nhập mã thuốc cần bán (Enter để kết thúc): ").strip()
        if code == "":
            break
        medicine = find_medicine(medicines, code)
        if medicine is None:
            print("Lỗi: thuốc không tồn tại.")
            continue
        if is_expired(medicine["han_su_dung"]):
            print(f"Lỗi: thuốc '{medicine['ten_thuoc']}' đã hết hạn sử dụng "
                  f"({medicine['han_su_dung']}), không được bán.")
            continue
        in_cart = sum(i["so_luong"] for i in cart if i["medicine"] is medicine)
        available = medicine["so_luong_ton"] - in_cart
        print(f"Thuốc: {medicine['ten_thuoc']} | Đơn giá: {money(medicine['don_gia'])} "
              f"| Còn bán được: {available} {medicine['don_vi_tinh']}")
        quantity = read_int("Số lượng bán: ", minimum=1)
        if quantity > available:
            print(f"Lỗi: số lượng bán vượt quá số lượng tồn (chỉ còn {available}).")
            continue
        cart.append({"medicine": medicine, "so_luong": quantity})
        print(f"Đã thêm vào hóa đơn: thành tiền "
              f"{money(calculate_total(medicine['don_gia'], quantity))} VNĐ.")

    if not cart:
        print("Hóa đơn trống, không có giao dịch nào được ghi nhận.")
        return

    # Lập hóa đơn và cập nhật kho chỉ sau khi mọi điều kiện đã hợp lệ
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total = 0.0
    print("\n" + LINE)
    print("               HÓA ĐƠN BÁN THUỐC")
    print(LINE)
    print(f"{'Tên thuốc':<22}{'SL':>4}{'Đơn giá':>11}{'Thành tiền':>13}")
    print("-" * 50)
    for item in cart:
        m, qty = item["medicine"], item["so_luong"]
        amount = calculate_total(m["don_gia"], qty)
        total += amount
        m["so_luong_ton"] -= qty
        m["so_luong_da_ban"] += qty
        sales.append({"thoi_gian": now, "ma_thuoc": m["ma_thuoc"], "ten_thuoc": m["ten_thuoc"],
                      "loai_thuoc": m["loai_thuoc"], "so_luong": qty,
                      "don_gia": m["don_gia"], "thanh_tien": amount})
        print(f"{m['ten_thuoc'][:21]:<22}{qty:>4}{money(m['don_gia']):>11}{money(amount):>13}")
    print("-" * 50)
    print(f"{'TỔNG TIỀN HÓA ĐƠN:':<37}{money(total):>13} VNĐ")
    print(LINE)
    print("Bán thuốc thành công, đã cập nhật số lượng tồn kho.")


# ---------------------------------------------------------------------------
# THỐNG KÊ
# ---------------------------------------------------------------------------
def statistics(medicines, sales):
    """Thống kê: số loại thuốc, giá trị tồn kho, bán chạy, sắp hết, doanh thu theo loại."""
    print("\n--- THỐNG KÊ ---")
    total_types = len(medicines)
    inventory_value = sum(m["don_gia"] * m["so_luong_ton"] for m in medicines)
    print(f"1. Tổng số loại thuốc        : {total_types}")
    print(f"2. Tổng giá trị hàng tồn kho : {money(inventory_value)} VNĐ")

    sold = [m for m in medicines if m["so_luong_da_ban"] > 0]
    if sold:
        best = max(m["so_luong_da_ban"] for m in sold)
        names = ", ".join(m["ten_thuoc"] for m in sold if m["so_luong_da_ban"] == best)
        print(f"3. Thuốc bán chạy nhất       : {names} (đã bán {best})")
    else:
        print("3. Thuốc bán chạy nhất       : chưa có giao dịch bán hàng")

    low_stock = [m for m in medicines if m["so_luong_ton"] <= LOW_STOCK_THRESHOLD]
    if low_stock:
        print(f"4. Thuốc sắp hết hàng (tồn <= {LOW_STOCK_THRESHOLD}):")
        for m in low_stock:
            print(f"     - {m['ma_thuoc']} {m['ten_thuoc']}: còn {m['so_luong_ton']} {m['don_vi_tinh']}")
    else:
        print(f"4. Thuốc sắp hết hàng        : không có (ngưỡng tồn <= {LOW_STOCK_THRESHOLD})")

    revenue = {}
    for s in sales:
        revenue[s["loai_thuoc"]] = revenue.get(s["loai_thuoc"], 0.0) + s["thanh_tien"]
    if revenue:
        print("5. Doanh thu theo loại thuốc:")
        for kind, value in sorted(revenue.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {kind:<16}: {money(value)} VNĐ")
        print(f"     Tổng doanh thu     : {money(sum(revenue.values()))} VNĐ")
    else:
        print("5. Doanh thu theo loại thuốc : chưa có doanh thu")

    # Mở rộng: cảnh báo hạn sử dụng
    expired = [m for m in medicines if days_to_expiry(m["han_su_dung"]) < 0]
    near = [m for m in medicines if 0 <= days_to_expiry(m["han_su_dung"]) <= NEAR_EXPIRY_DAYS]
    print(f"6. Cảnh báo hạn sử dụng      : {len(expired)} loại đã hết hạn, "
          f"{len(near)} loại hết hạn trong {NEAR_EXPIRY_DAYS} ngày tới")


# ---------------------------------------------------------------------------
# LƯU VÀ ĐỌC FILE TXT
# ---------------------------------------------------------------------------
def save_data(medicines, sales, medicine_file=MEDICINE_FILE, sales_file=SALES_FILE):
    """Ghi danh mục thuốc và lịch sử bán hàng ra tệp TXT (UTF-8)."""
    try:
        with open(medicine_file, "w", encoding="utf-8") as f:
            for m in medicines:
                f.write(SEPARATOR.join([
                    m["ma_thuoc"], m["ten_thuoc"], m["loai_thuoc"], m["don_vi_tinh"],
                    str(m["don_gia"]), str(m["so_luong_ton"]), m["han_su_dung"],
                    m["nha_cung_cap"], str(m["so_luong_da_ban"])]) + "\n")
        with open(sales_file, "w", encoding="utf-8") as f:
            for s in sales:
                f.write(SEPARATOR.join([
                    s["thoi_gian"], s["ma_thuoc"], s["ten_thuoc"], s["loai_thuoc"],
                    str(s["so_luong"]), str(s["don_gia"]), str(s["thanh_tien"])]) + "\n")
        print(f"Lưu dữ liệu thành công ({len(medicines)} loại thuốc, {len(sales)} giao dịch).")
        return True
    except OSError as error:
        print("Lỗi: không thể ghi file:", error)
        return False


def parse_medicine_line(line):
    """Chuyển một dòng TXT thành dictionary thuốc; ném ValueError nếu sai cấu trúc."""
    parts = line.split(SEPARATOR)
    if len(parts) != 9:
        raise ValueError("sai số lượng trường")
    try:
        medicine = {
            "ma_thuoc": parts[0], "ten_thuoc": parts[1], "loai_thuoc": parts[2],
            "don_vi_tinh": parts[3], "don_gia": float(parts[4]), "so_luong_ton": int(parts[5]),
            "han_su_dung": parts[6], "nha_cung_cap": parts[7], "so_luong_da_ban": int(parts[8]),
        }
        parse_date(medicine["han_su_dung"])
    except ValueError:
        raise ValueError("sai kiểu dữ liệu số hoặc ngày") from None
    if medicine["don_gia"] <= 0 or medicine["so_luong_ton"] < 0 or medicine["so_luong_da_ban"] < 0:
        raise ValueError("giá trị số không hợp lệ")
    return medicine


def parse_sale_line(line):
    """Chuyển một dòng TXT thành dictionary giao dịch; ném ValueError nếu sai cấu trúc."""
    parts = line.split(SEPARATOR)
    if len(parts) != 7:
        raise ValueError("sai số lượng trường")
    try:
        return {"thoi_gian": parts[0], "ma_thuoc": parts[1], "ten_thuoc": parts[2],
                "loai_thuoc": parts[3], "so_luong": int(parts[4]),
                "don_gia": float(parts[5]), "thanh_tien": float(parts[6])}
    except ValueError:
        raise ValueError("sai kiểu dữ liệu số") from None


def read_file(filename, parser):
    """Đọc một tệp TXT; trả về (danh sách bản ghi hợp lệ, số dòng lỗi) hoặc (None, 0) nếu không đọc được."""
    records, errors = [], 0
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(parser(line))
                except ValueError as error:
                    errors += 1
                    print(f"Cảnh báo: bỏ qua dòng {number} của '{filename}' ({error}).")
    except FileNotFoundError:
        print(f"Không tìm thấy file '{filename}'.")
        return None, 0
    except (OSError, UnicodeDecodeError) as error:
        print(f"Lỗi: không thể đọc file '{filename}':", error)
        return None, 0
    return records, errors


def load_data(medicine_file=MEDICINE_FILE, sales_file=SALES_FILE):
    """Đọc dữ liệu từ tệp TXT. Trả về (medicines, sales); file lỗi/thiếu thì trả về danh sách rỗng."""
    medicines, med_errors = read_file(medicine_file, parse_medicine_line)
    sales, sale_errors = read_file(sales_file, parse_sale_line)
    if medicines is None:
        print("Khởi tạo danh sách thuốc rỗng.")
        medicines = []
    if sales is None:
        sales = []
    print(f"Đã đọc {len(medicines)} loại thuốc và {len(sales)} giao dịch từ file.")
    return medicines, sales


# ---------------------------------------------------------------------------
# MENU VÀ CHƯƠNG TRÌNH CHÍNH
# ---------------------------------------------------------------------------
def show_menu():
    print("\n" + LINE)
    print("           QUẢN LÝ HIỆU THUỐC")
    print(LINE)
    print("1. Thêm thuốc")
    print("2. Hiển thị danh sách")
    print("3. Cập nhật thuốc")
    print("4. Xóa thuốc")
    print("5. Tìm kiếm")
    print("6. Sắp xếp")
    print("7. Bán thuốc")
    print("8. Thống kê")
    print("9. Lưu dữ liệu")
    print("10. Đọc dữ liệu")
    print("0. Thoát")
    print(LINE)


def main():
    medicines, sales = load_data()
    while True:
        show_menu()
        try:
            choice = input("Lựa chọn: ").strip()
        except EOFError:
            choice = "0"
        if choice == "1":
            add_medicine(medicines)
        elif choice == "2":
            display_medicines(medicines)
        elif choice == "3":
            update_medicine(medicines)
        elif choice == "4":
            delete_medicine(medicines)
        elif choice == "5":
            search_medicines(medicines)
        elif choice == "6":
            sort_menu(medicines)
        elif choice == "7":
            sell_medicine(medicines, sales)
        elif choice == "8":
            statistics(medicines, sales)
        elif choice == "9":
            save_data(medicines, sales)
        elif choice == "10":
            if confirm("Dữ liệu đang làm việc sẽ bị thay thế. Tiếp tục (y/n)? "):
                medicines, sales = load_data()
        elif choice == "0":
            save_data(medicines, sales)
            print("Tạm biệt!")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng chọn lại.")


if __name__ == "__main__":
    main()
