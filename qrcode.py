import qrcode

# 🔹 Replace this with your APK's direct download link
apk_url = "https://drive.google.com/uc?id=1fJAQ3ivmU5v9d3YwhKvMxkawUqv3fpCJ"

# Generate QR code
qr = qrcode.QRCode(
    version=1,  # controls the size of the QR code (1 = smallest)
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(apk_url)
qr.make(fit=True)

# Create and save image
img = qr.make_image(fill_color="black", back_color="white")
img.save("apk_qr.png")

print("✅ QR code generated and saved as apk_qr.png")
