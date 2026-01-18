# Mock In-Memory Database representing the core banking user records.
# Keys represent the National ID (NIK) and values contain user profile details.
DATABASE_USER = {
    "1234567890123456": {
        "nama": "Arif Athaya",
        "email": "arif@example.com",
        "tgl_lahir": "04-10-2005",
        "phone": "08123456789",
        "alamat": "Jl. Emerald Alona G 43",
        "saldo": 2000000,
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
    """
    Encapsulates backend tools for wallet operations.
    
    This class handles logic for authentication, requests, and transactions,
    utilizing a secure context (Vault) to access redacted PII data.
    """
    def __init__(self):
        # Stores the temporary decrypted PII data for the current request
        self.current_session_context = {}

    def set_context(self, session_data: dict):
        """
        Injects the secure 'Vault' data from the Guardrail Service
        into the tool's execution context.
        """
        self.current_session_context = session_data

    def ganti_password(self, nik_tag: str, email_tag: str, birthdate_tag: str):
        """
        Initiates a password reset process by verifying user identity.
        
        Validates NIK, Email, and Date of Birth against the database.
        """
        # Retrieve real values from the secure vault using redacted tags
        real_nik = self.current_session_context.get(nik_tag)
        real_email = self.current_session_context.get(email_tag)
        real_birthdate = self.current_session_context.get(birthdate_tag)

        # Ensure all required PII data is present in the session
        if not all([real_nik, real_email, real_birthdate]):
            return "GAGAL: Data NIK, Email, atau Tanggal Lahir tidak lengkap/sesi invalid."

        # Database lookup
        user = DATABASE_USER.get(real_nik)
        if not user:
            return f"GAGAL: NIK {real_nik} tidak terdaftar."

        # Verify if input data matches the stored user profile
        if user['email'].lower() == real_email.lower() and user['tgl_lahir'] == real_birthdate:
            return f"BERHASIL: Link reset password dikirim ke {real_email}."
        else:
            return "GAGAL: Data tidak cocok."

    def request_kartu_fisik(self, nama_tag: str, alamat_tag: str, phone_tag: str):
        """
        Processes a request for a physical debit card delivery.
        """
        # Resolve real entity values from the secure context
        real_nama = self.current_session_context.get(nama_tag)
        real_alamat = self.current_session_context.get(alamat_tag)
        real_phone = self.current_session_context.get(phone_tag)

        # Validation check for required shipping details
        if not all([real_nama, real_alamat, real_phone]):
            return "GAGAL: Data identitas pengiriman tidak lengkap."

        return {
            "status": "DIPROSES",
            "message": f"Kartu fisik a.n '{real_nama}' akan dikirim ke '{real_alamat}'."
        }

    def withdraw_ke_bank(self, nik_tag: str, bank_num_tag: str, nama_pemilik_tag: str):
        """
        Executes a fund withdrawal to an external bank account.
        
        Performs validation on account ownership and balance sufficiency.
        """
        # Retrieve transaction details from the vault
        real_nik = self.current_session_context.get(nik_tag)
        real_bank_num = self.current_session_context.get(bank_num_tag)
        real_nama_pemilik = self.current_session_context.get(nama_pemilik_tag)

        # Validate transaction inputs
        if not all([real_nik, real_bank_num, real_nama_pemilik]):
            return "GAGAL: Data transaksi tidak lengkap."

        user = DATABASE_USER.get(real_nik)
        if not user: 
            return "GAGAL: User tidak ditemukan."

        # Security Check: Ensure the destination account name matches the user's name
        if real_nama_pemilik.lower() not in user['nama'].lower():
            return f"GAGAL: Nama pemilik rekening ({real_nama_pemilik}) TIDAK SESUAI akun."

        # Check for minimum balance requirement
        if user['saldo'] < 50000:
            return f"GAGAL: Saldo {user['saldo']} kurang dari min. 50.000."
        
        # Deduct balance and commit transaction
        user['saldo'] -= 50000
        
        return {
            "status": "BERHASIL",
            "message": f"Transfer ke {real_bank_num} berhasil. Sisa saldo: {user['saldo']}"
        }