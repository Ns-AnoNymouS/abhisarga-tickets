import cv2
import qrcode

import time
import random


def overlay_image(background_path, overlay_path, x, y, height):
    """
    Places overlay image on top of the background image at position (x, y) with a specified height.
    The width is adjusted to maintain the aspect ratio.
    """
    background = cv2.imread(background_path)
    overlay = cv2.imread(overlay_path)
    bg_h, bg_w, _ = background.shape
    ol_h, ol_w, _ = overlay.shape

    # Calculate new width while maintaining aspect ratio
    aspect_ratio = ol_w / ol_h
    new_width = int(height * aspect_ratio)

    # Resize overlay
    overlay_resized = cv2.resize(overlay, (new_width, height))
    ol_h, ol_w, _ = overlay_resized.shape  # Update dimensions

    # Ensure overlay doesn't go out of bounds
    if x + ol_w > bg_w:
        ol_w = bg_w - x
        overlay_resized = overlay_resized[:, :ol_w]  # Crop width
    if y + ol_h > bg_h:
        ol_h = bg_h - y
        overlay_resized = overlay_resized[:ol_h, :]  # Crop height

    # Create a mask
    overlay_gray = cv2.cvtColor(overlay_resized, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(overlay_gray, 1, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    # Extract regions of interest (ROI)
    bg_roi = background[y : y + ol_h, x : x + ol_w]
    bg_with_mask = cv2.bitwise_and(bg_roi, bg_roi, mask=mask_inv)
    overlay_with_mask = cv2.bitwise_and(overlay_resized, overlay_resized, mask=mask)

    # Combine background and overlay
    result = cv2.add(bg_with_mask, overlay_with_mask)
    background[y : y + ol_h, x : x + ol_w] = result

    return background

def generate_qr(text, filename="qrcode.png"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    img = qr.make_image(fill="black", back_color="white")
    img.save(filename)
    print(f"QR code saved as {filename}")

def generate_final_ticket():
    unique_id = f"AB{random.randint(1000, 9999)}{int(time.time() * 1000)}"
    print(f"Unique ID: {unique_id}")
    generate_qr(unique_id)
    # Overlay image with height constraint
    output = overlay_image(
        background_path="background.png",
        overlay_path="qrcode.png",
        x=1544,
        y=470,
        height=152,
    )

    # Save and display
    cv2.imwrite("output2.jpg", output)
    # cv2.imshow("Result", output)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

generate_final_ticket()