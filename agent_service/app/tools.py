DATABASE_USER = {
    "1234567890123456": {
        "nama": "Arif Athaya",
        "email": "arif@example.com",
        "tgl_lahir": "04-10-2005",
        "phone": "08123456789",
        "alamat": "Jl. Emerald Alona G 43",
        "saldo": 5000000,
        "pin": "123456"
    },
    "3201123456789001": {
        "nama": "Budi Santoso",
        "email": "budi@test.com",
        "tgl_lahir": "17-08-1990",
        "phone": "089988776655",
        "alamat": "Jl. Sudirman No 1 Jakarta",
        "saldo": 150000,
        "pin": "654321"
    }
}

class WalletTools:
    def __init__(self):
        self.current_session_context = {}

    def set_context(self, session_data: dict):
        """
        Menerima data rahasia (Vault) dari Guardrail Service 
        untuk digunakan dalam eksekusi tools saat ini.
        """
        self.current_session_context = session_data

    def ganti_password(self, nik_tag: str, email_tag: str, birthdate_tag: str):
        """
        Mengganti password akun. Memverifikasi NIK, Email, dan Tanggal Lahir user.
        """
        real_nik = self.current_session_context.get(nik_tag)
        real_email = self.current_session_context.get(email_tag)
        real_birthdate = self.current_session_context.get(birthdate_tag)

        if not all([real_nik, real_email, real_birthdate]):
            return "GAGAL: Data NIK, Email, atau Tanggal Lahir tidak lengkap/sesi invalid."

        user = DATABASE_USER.get(real_nik)
        if not user:
            return f"GAGAL: NIK {real_nik} tidak terdaftar."

        if user['email'].lower() == real_email.lower() and user['tgl_lahir'] == real_birthdate:
            return f"BERHASIL: Link reset password dikirim ke {real_email}."
        else:
            return "GAGAL: Data tidak cocok."

    def request_kartu_fisik(self, nama_tag: str, alamat_tag: str, phone_tag: str):
        """
        Request kartu debit fisik.
        """
        real_nama = self.current_session_context.get(nama_tag)
        real_alamat = self.current_session_context.get(alamat_tag)
        real_phone = self.current_session_context.get(phone_tag)

        if not all([real_nama, real_alamat, real_phone]):
            return "GAGAL: Data identitas pengiriman tidak lengkap."

        return {
            "status": "DIPROSES",
            "message": f"Kartu fisik a.n '{real_nama}' akan dikirim ke '{real_alamat}'."
        }

    def withdraw_ke_bank(self, nik_tag: str, bank_num_tag: str, nama_pemilik_tag: str):
        """
        Pencairan saldo (Withdraw) ke rekening Bank.
        """
        real_nik = self.current_session_context.get(nik_tag)
        real_bank_num = self.current_session_context.get(bank_num_tag)
        real_nama_pemilik = self.current_session_context.get(nama_pemilik_tag)

        if not all([real_nik, real_bank_num, real_nama_pemilik]):
            return "GAGAL: Data transaksi tidak lengkap."

        user = DATABASE_USER.get(real_nik)
        if not user: 
            return "GAGAL: User tidak ditemukan."

        if real_nama_pemilik.lower() not in user['nama'].lower():
            return f"GAGAL: Nama pemilik rekening ({real_nama_pemilik}) TIDAK SESUAI akun."

        if user['saldo'] < 50000:
            return f"GAGAL: Saldo {user['saldo']} kurang dari min. 50.000."
        
        user['saldo'] -= 50000
        
        return {
            "status": "BERHASIL",
            "message": f"Transfer ke {real_bank_num} berhasil. Sisa saldo: {user['saldo']}"
        }
