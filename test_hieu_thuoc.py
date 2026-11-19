# -*- coding: utf-8 -*-
"""
Chạy tự động các test case cho chương trình quản lý hiệu thuốc.
Mỗi test case chạy chương trình thật (main.py) với dữ liệu nhập giả lập, ghi lại
kết quả thực tế và đánh giá Đạt/Không đạt. Kết quả được lưu vào test_results.json.

Cách chạy:  python test_hieu_thuoc.py
"""
import builtins
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_MED = os.path.join(HERE, "medicines_goc.txt")
SEED_SALES = os.path.join(HERE, "sales_goc.txt")


def load_module():
    spec = importlib.util.spec_from_file_location("main_under_test", os.path.join(HERE, "main.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_session(inputs, med_text=None, sales_text=None):
    """Chạy main() với dữ liệu nhập giả lập (có hiển thị phần nhập như trên Console).
    Trả về (output, medicines_after, sales_after) đọc lại từ file sau khi thoát."""
    work = tempfile.mkdtemp()
    old = os.getcwd()
    try:
        if med_text is False:
            pass                      # không tạo file để kiểm tra trường hợp file không tồn tại
        elif med_text is None:
            shutil.copy(SEED_MED, os.path.join(work, "medicines.txt"))
        else:
            with open(os.path.join(work, "medicines.txt"), "w", encoding="utf-8") as f:
                f.write(med_text)
        if sales_text is False:
            pass
        elif sales_text is None:
            shutil.copy(SEED_SALES, os.path.join(work, "sales.txt"))
        else:
            with open(os.path.join(work, "sales.txt"), "w", encoding="utf-8") as f:
                f.write(sales_text)
        os.chdir(work)
        module = load_module()
        it = iter(list(inputs) + ["0"])

        def fake_input(prompt=""):
            try:
                answer = next(it)
            except StopIteration:
                raise EOFError
            sys.stdout.write(f"{prompt}{answer}\n")
            return answer

        buf = io.StringIO()
        real_input = builtins.input
        builtins.input = fake_input
        try:
            with contextlib.redirect_stdout(buf):
                module.main()
        finally:
            builtins.input = real_input
        meds, _ = module.read_file("medicines.txt", module.parse_medicine_line)
        sales, _ = module.read_file("sales.txt", module.parse_sale_line)
        return buf.getvalue(), meds or [], sales or []
    finally:
        os.chdir(old)
        shutil.rmtree(work, ignore_errors=True)


def get(meds, code):
    for m in meds:
        if m["ma_thuoc"] == code:
            return m
    return None


RESULTS = []


def record(chuc_nang, du_lieu, mong_doi, thuc_te, ok):
    RESULTS.append({"tt": len(RESULTS) + 1, "chuc_nang": chuc_nang, "du_lieu": du_lieu,
                    "mong_doi": mong_doi, "thuc_te": thuc_te, "dat": bool(ok)})


def main():
    mod = load_module()
    today = date.today()

    # ---------- THÊM THUỐC ----------
    out, meds, _ = run_session(["1", "T011", "Loratadin 10mg", "Dị ứng", "Hộp", "32000", "30",
                                "31/12/2028", "Dược ABC"])
    m = get(meds, "T011")
    record("Thêm thuốc", "Mã T011 mới, các trường hợp lệ", "Thêm thành công, danh sách có 11 thuốc",
           f"Thông báo thành công; danh sách có {len(meds)} thuốc, T011 tồn {m['so_luong_ton'] if m else '-'}",
           "Thêm thuốc thành công." in out and len(meds) == 11 and m and m["so_luong_ton"] == 30)

    out, meds, _ = run_session(["1", "T001", "T012", "Zinc 10mg", "Khoáng chất", "Hộp", "45000", "20",
                                "30/11/2028", "Dược ABC"])
    ok = ("mã thuốc đã tồn tại" in out and len(meds) == 11
          and sum(1 for x in meds if x["ma_thuoc"] == "T001") == 1 and get(meds, "T012"))
    record("Thêm thuốc", "Nhập mã T001 (đã tồn tại), sau đó nhập T012",
           "Báo mã trùng, yêu cầu nhập lại, không tạo bản ghi trùng",
           "Báo lỗi mã trùng, yêu cầu nhập lại; chỉ có 1 thuốc mã T001, thêm được T012", ok)

    out, meds, _ = run_session(["1", "T013", "Test A", "Loại", "Hộp", "0", "-5", "abc", "10000", "5",
                                "01/01/2028", "NCC"])
    ok = out.count("Lỗi") >= 3 and get(meds, "T013") and get(meds, "T013")["don_gia"] == 10000
    record("Thêm thuốc", "Đơn giá lần lượt nhập 0, -5, abc, rồi 10000",
           "Từ chối 3 giá trị đầu, chấp nhận 10000",
           f"Hiển thị {out.count('Lỗi')} thông báo lỗi; lưu đơn giá {get(meds, 'T013')['don_gia']:,.0f}",
           ok)

    out, meds, _ = run_session(["1", "T014", "Test B", "Loại", "Hộp", "5000", "-3", "x", "7",
                                "01/01/2028", "NCC"])
    ok = out.count("Lỗi") >= 2 and get(meds, "T014") and get(meds, "T014")["so_luong_ton"] == 7
    record("Thêm thuốc", "Số lượng tồn nhập -3, x, rồi 7", "Từ chối -3 và x, chấp nhận 7",
           f"Hiển thị {out.count('Lỗi')} thông báo lỗi; lưu số lượng tồn {get(meds, 'T014')['so_luong_ton']}", ok)

    out, meds, _ = run_session(["1", "T015", "Test C", "Loại", "Hộp", "5000", "7",
                                "31-12-2027", "32/13/2027", "31/12/2027", "NCC"])
    ok = out.count("ngày không hợp lệ") == 2 and get(meds, "T015") and get(meds, "T015")["han_su_dung"] == "31/12/2027"
    record("Thêm thuốc", "Hạn sử dụng nhập 31-12-2027, 32/13/2027, rồi 31/12/2027",
           "Từ chối hai ngày sai, chấp nhận ngày đúng",
           f"Báo lỗi ngày không hợp lệ {out.count('ngày không hợp lệ')} lần; lưu HSD {get(meds, 'T015')['han_su_dung']}", ok)

    # ---------- HIỂN THỊ ----------
    out, meds, _ = run_session(["2"])
    rows = [l for l in out.splitlines() if l[:1] == "T" and l[1:4].isdigit()]
    ok = len(rows) == 10 and "(*)" in out
    record("Hiển thị", "Danh sách mẫu gồm 10 thuốc", "Hiển thị đủ 10 dòng, đánh dấu thuốc hết hạn",
           f"Hiển thị {len(rows)} dòng; thuốc T005 hết hạn được đánh dấu dấu *", ok)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.display_medicines([])
    record("Hiển thị", "Danh sách thuốc rỗng", "Thông báo danh sách rỗng, không in bảng",
           "Thông báo: danh sách thuốc hiện đang rỗng", "đang rỗng" in buf.getvalue())

    # ---------- TÌM KIẾM ----------
    out, _, _ = run_session(["5", "1", "T003"])
    record("Tìm kiếm", "Theo mã thuốc: T003", "Hiển thị đúng thuốc Amoxicillin 500mg",
           "Hiển thị 1 kết quả: Amoxicillin 500mg", "Amoxicillin" in out and "Tổng cộng: 1 loại" in out)

    out, _, _ = run_session(["5", "2", "vitamin"])
    record("Tìm kiếm", "Theo tên: 'vitamin' (chữ thường, khớp một phần)", "Hiển thị Vitamin C 500mg và Vitamin B1",
           "Hiển thị 2 kết quả: T002 và T010", "Tổng cộng: 2 loại" in out and "T002" in out and "T010" in out)

    out, _, _ = run_session(["5", "3", "kháng sinh"])
    record("Tìm kiếm", "Theo loại thuốc: 'kháng sinh'", "Hiển thị thuốc thuộc nhóm Kháng sinh",
           "Hiển thị 1 kết quả: T003", "Tổng cộng: 1 loại" in out and "T003" in out)

    out, _, _ = run_session(["5", "4", "DOMESCO"])
    record("Tìm kiếm", "Theo nhà cung cấp: 'DOMESCO' (chữ hoa)", "Hiển thị các thuốc của Domesco",
           "Hiển thị 2 kết quả: T004 và T006", "Tổng cộng: 2 loại" in out and "T004" in out and "T006" in out)

    out, _, _ = run_session(["5", "2", "thuốc không có"])
    record("Tìm kiếm", "Theo tên: 'thuốc không có'", "Thông báo không tìm thấy",
           "Thông báo: Không tìm thấy thuốc phù hợp", "Không tìm thấy thuốc phù hợp" in out)

    # ---------- CẬP NHẬT ----------
    out, meds, _ = run_session(["3", "T002", "", "", "", "", "", "36000", "", "", ])
    m = get(meds, "T002")
    ok = "Cập nhật thông tin thuốc thành công" in out and m["don_gia"] == 36000 and m["so_luong_ton"] == 40
    record("Cập nhật", "Mã T002; đơn giá mới 36000, các trường khác nhấn Enter",
           "Chỉ đơn giá thay đổi, các trường khác giữ nguyên",
           f"Cập nhật thành công; đơn giá {m['don_gia']:,.0f}, tồn vẫn {m['so_luong_ton']}", ok)

    out, _, _ = run_session(["3", "T999"])
    record("Cập nhật", "Mã thuốc T999 không tồn tại", "Thông báo thuốc không tồn tại",
           "Thông báo: Thuốc không tồn tại", "Thuốc không tồn tại" in out)

    out, meds, _ = run_session(["3", "T002", "T001", "T020", "", "", "", "", "", "", ""])
    ok = "đã tồn tại ở thuốc khác" in out and get(meds, "T020") and not get(meds, "T002")
    record("Cập nhật", "Đổi mã T002 sang T001 (trùng), sau đó đổi sang T020",
           "Từ chối mã trùng, chấp nhận mã mới T020",
           "Báo lỗi mã trùng với thuốc khác; mã được đổi thành T020", ok)

    # ---------- XÓA ----------
    out, meds, _ = run_session(["4", "T010", "y"])
    record("Xóa", "Mã T010, xác nhận y", "Xóa thành công, còn 9 thuốc",
           f"Thông báo đã xóa; danh sách còn {len(meds)} thuốc", "Đã xóa thuốc" in out and len(meds) == 9 and not get(meds, "T010"))

    out, meds, _ = run_session(["4", "T010", "n"])
    record("Xóa", "Mã T010, trả lời n", "Hủy xóa, danh sách vẫn đủ 10 thuốc",
           f"Thông báo hủy thao tác; danh sách vẫn có {len(meds)} thuốc", "Đã hủy thao tác xóa" in out and len(meds) == 10)

    out, _, _ = run_session(["4", "T999"])
    record("Xóa", "Mã thuốc T999 không tồn tại", "Thông báo thuốc không tồn tại",
           "Thông báo: Thuốc không tồn tại", "Thuốc không tồn tại" in out)

    # ---------- SẮP XẾP ----------
    out, _, _ = run_session(["6", "2", "1"])
    seg = out.split("DANH SÁCH SAU KHI SẮP XẾP")[1]
    codes = [l[:4] for l in seg.splitlines() if l[:1] == "T" and l[1:4].isdigit()]
    ok = codes[0] == "T006" and codes[-1] == "T005"
    record("Sắp xếp", "Theo đơn giá, tăng dần", "Đơn giá tăng dần: T006 (5,000) đầu, T005 (85,000) cuối",
           f"Thứ tự mã: {', '.join(codes)}", ok)

    out, _, _ = run_session(["6", "1", "2"])
    seg = out.split("DANH SÁCH SAU KHI SẮP XẾP")[1]
    codes = [l[:4] for l in seg.splitlines() if l[:1] == "T" and l[1:4].isdigit()]
    names = [mm["ten_thuoc"] for mm in mod.sort_medicines(
        [mod.parse_medicine_line(l.strip()) for l in open(SEED_MED, encoding="utf-8") if l.strip()],
        "ten_thuoc", True)]
    ok = names[0] == "Vitamin C 500mg" and names[-1] == "Amoxicillin 500mg"
    record("Sắp xếp", "Theo tên thuốc, giảm dần", "Tên giảm dần theo bảng chữ cái (Vitamin C ... Amoxicillin)",
           f"Tên đầu: {names[0]}; tên cuối: {names[-1]}", ok)

    out, _, _ = run_session(["6", "3", "1"])
    seg = out.split("DANH SÁCH SAU KHI SẮP XẾP")[1]
    codes = [l[:4] for l in seg.splitlines() if l[:1] == "T" and l[1:4].isdigit()]
    ok = codes[0] == "T003" and codes[-1] == "T006"
    record("Sắp xếp", "Theo số lượng tồn, tăng dần", "Tồn tăng dần: T003 (3) đầu, T006 (100) cuối",
           f"Thứ tự mã: {', '.join(codes)}", ok)

    # ---------- BÁN THUỐC ----------
    out, meds, sales = run_session(["7", "T001", "2", ""])
    m = get(meds, "T001")
    ok = "50,000" in out and m["so_luong_ton"] == 48 and m["so_luong_da_ban"] == 16 and len(sales) == 6
    record("Bán thuốc", "Bán T001 (tồn 50, giá 25,000), số lượng 2", "Thành tiền 50,000; tồn còn 48; đã bán 16",
           f"Hóa đơn 50,000 VNĐ; tồn {m['so_luong_ton']}; đã bán {m['so_luong_da_ban']}; lịch sử có {len(sales)} giao dịch", ok)

    out, meds, _ = run_session(["7", "T001", "2", "T002", "1", ""])
    ok = "85,000 VNĐ" in out and get(meds, "T001")["so_luong_ton"] == 48 and get(meds, "T002")["so_luong_ton"] == 39
    record("Bán thuốc", "Hóa đơn gồm T001 x2 và T002 x1", "Tổng tiền 85,000; tồn T001 = 48, T002 = 39",
           f"Tổng hóa đơn 85,000 VNĐ; tồn T001 = {get(meds, 'T001')['so_luong_ton']}, T002 = {get(meds, 'T002')['so_luong_ton']}", ok)

    out, meds, sales = run_session(["7", "T003", "5", ""])
    ok = "vượt quá số lượng tồn" in out and get(meds, "T003")["so_luong_ton"] == 3 and len(sales) == 5
    record("Bán thuốc", "Bán T003 (tồn 3) số lượng 5", "Từ chối, tồn kho không đổi, không ghi giao dịch",
           f"Báo vượt tồn; tồn T003 vẫn {get(meds, 'T003')['so_luong_ton']}; lịch sử vẫn {len(sales)} giao dịch", ok)

    out, meds, sales = run_session(["7", "T005", ""])
    ok = "đã hết hạn sử dụng" in out and get(meds, "T005")["so_luong_ton"] == 20 and len(sales) == 5
    record("Bán thuốc", "Bán T005 (HSD 10/09/2026, đã hết hạn)", "Từ chối giao dịch, tồn kho không đổi",
           f"Báo thuốc hết hạn; tồn T005 vẫn {get(meds, 'T005')['so_luong_ton']}; không ghi nhận doanh thu", ok)

    out, _, sales = run_session(["7", "T999", ""])
    record("Bán thuốc", "Mã thuốc T999 không tồn tại", "Thông báo thuốc không tồn tại",
           "Thông báo: Thuốc không tồn tại; không có giao dịch", "thuốc không tồn tại" in out and len(sales) == 5)

    out, meds, _ = run_session(["7", "T001", "abc", "0", "-1", "3", ""])
    ok = out.count("Lỗi") >= 3 and get(meds, "T001")["so_luong_ton"] == 47
    record("Bán thuốc", "Số lượng bán nhập abc, 0, -1, rồi 3", "Từ chối ba giá trị sai, chấp nhận 3",
           f"Báo lỗi {out.count('Lỗi')} lần; tồn T001 còn {get(meds, 'T001')['so_luong_ton']}", ok)

    out, meds, _ = run_session(["7", "T003", "2", "T003", "2", ""])
    ok = "chỉ còn 1" in out and get(meds, "T003")["so_luong_ton"] == 1
    record("Bán thuốc", "Cùng hóa đơn: T003 x2 rồi T003 x2 (tồn 3)", "Lần thứ hai bị từ chối vì chỉ còn 1",
           f"Lần 2 báo chỉ còn 1; sau giao dịch tồn T003 = {get(meds, 'T003')['so_luong_ton']}", ok)

    # ---------- THỐNG KÊ ----------
    seed = [mod.parse_medicine_line(l.strip()) for l in open(SEED_MED, encoding="utf-8") if l.strip()]
    inv = sum(x["don_gia"] * x["so_luong_ton"] for x in seed)
    out, _, _ = run_session(["8"])
    ok = (f"{inv:,.0f} VNĐ" in out and "Paracetamol 500mg (đã bán 14)" in out
          and "T003" in out and "T007" in out and "747,000 VNĐ" in out and "Tổng số loại thuốc        : 10" in out)
    record("Thống kê", "Dữ liệu mẫu 10 thuốc, 5 giao dịch",
           f"10 loại; giá trị tồn {inv:,.0f}; bán chạy Paracetamol; sắp hết T003, T007; doanh thu 747,000",
           f"10 loại; giá trị tồn {inv:,.0f}; bán chạy Paracetamol (14); sắp hết T003, T007; tổng doanh thu 747,000", ok)

    zero_sold = "".join("|".join(l.strip().split("|")[:8] + ["0"]) + "\n"
                        for l in open(SEED_MED, encoding="utf-8") if l.strip())
    out, _, _ = run_session(["8"], med_text=zero_sold, sales_text="")
    record("Thống kê", "Chưa có giao dịch bán hàng (sales.txt rỗng, số lượng đã bán = 0)", "Báo chưa có giao dịch/doanh thu, không lỗi",
           "Hiển thị: chưa có giao dịch bán hàng; chưa có doanh thu",
           "chưa có giao dịch bán hàng" in out and "chưa có doanh thu" in out)

    # ---------- FILE ----------
    out, meds, sales = run_session(["1", "T016", "Test D", "Loại", "Hộp", "1000", "9", "01/01/2029", "NCC", "9"])
    ok = "Lưu dữ liệu thành công" in out and get(meds, "T016") is not None
    record("File", "Thêm T016, chọn Lưu dữ liệu (9) rồi thoát", "Ghi file thành công; đọc lại có T016",
           f"Thông báo lưu thành công; đọc lại file có {len(meds)} thuốc, gồm T016", ok)

    work = tempfile.mkdtemp()
    old = os.getcwd()
    os.chdir(work)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m_list, s_list = mod.load_data("khong_ton_tai.txt", "khong_ton_tai_2.txt")
    os.chdir(old)
    shutil.rmtree(work, ignore_errors=True)
    ok = m_list == [] and s_list == [] and "Không tìm thấy file" in buf.getvalue()
    record("File", "Đọc file không tồn tại", "Thông báo, khởi tạo danh sách rỗng, chương trình không dừng",
           "Thông báo không tìm thấy file; trả về danh sách rỗng, không phát sinh lỗi", ok)

    bad = open(SEED_MED, encoding="utf-8").read() + "T099|Dòng lỗi|thiếu trường\nT098|Sai số|Loại|Hộp|abc|5|01/01/2028|NCC|0\n"
    out, meds, _ = run_session(["2"], med_text=bad)
    ok = out.count("Cảnh báo: bỏ qua dòng") == 2 and "Đã đọc 10 loại thuốc" in out
    record("File", "File có thêm 2 dòng sai cấu trúc/sai kiểu số", "Bỏ qua 2 dòng lỗi, vẫn đọc 10 dòng hợp lệ",
           f"Cảnh báo bỏ qua {out.count('Cảnh báo: bỏ qua dòng')} dòng; đọc được 10 thuốc", ok)

    # ---------- MENU ----------
    out, _, _ = run_session(["abc", "99"])
    record("Menu", "Nhập lựa chọn abc và 99", "Thông báo lựa chọn không hợp lệ và hiển thị lại menu",
           f"Báo 'Lựa chọn không hợp lệ' {out.count('Lựa chọn không hợp lệ')} lần; menu hiển thị lại", out.count("Lựa chọn không hợp lệ") == 2)

    passed = sum(1 for r in RESULTS if r["dat"])
    print(f"Tổng số test case: {len(RESULTS)} | Đạt: {passed} | Không đạt: {len(RESULTS) - passed}")
    for r in RESULTS:
        print(f"{r['tt']:>2}. [{'ĐẠT' if r['dat'] else 'KHÔNG ĐẠT'}] {r['chuc_nang']}: {r['du_lieu']} -> {r['thuc_te']}")
    with open(os.path.join(HERE, "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
