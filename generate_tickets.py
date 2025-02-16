import cv2
import numpy as np

def overlay_image(background, overlay, x, y):
    """
    Places overlay image on top of the background image at position (x, y).
    """
    bg_h, bg_w, _ = background.shape
    ol_h, ol_w, _ = overlay.shape
    
    # Ensure overlay doesn't go out of bounds
    if x + ol_w > bg_w:
        ol_w = bg_w - x
    if y + ol_h > bg_h:
        ol_h = bg_h - y
    
    overlay_resized = overlay[:ol_h, :ol_w]
    
    # Create a mask from overlay
    overlay_gray = cv2.cvtColor(overlay_resized, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(overlay_gray, 1, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    
    # Get background and overlay ROI
    bg_roi = background[y:y+ol_h, x:x+ol_w]
    bg_with_mask = cv2.bitwise_and(bg_roi, bg_roi, mask=mask_inv)
    overlay_with_mask = cv2.bitwise_and(overlay_resized, overlay_resized, mask=mask)
    
    # Combine the images
    result = cv2.add(bg_with_mask, overlay_with_mask)
    background[y:y+ol_h, x:x+ol_w] = result
    
    return background

# Load images
bg_img = cv2.imread("background.png")
ol_img = cv2.imread("qrcode.png")

# Define position (x, y)
x, y = 50, 100

# Overlay image
output = overlay_image(bg_img, ol_img, x, y)

# Save and display
cv2.imwrite("output.jpg", output)
cv2.imshow("Result", output)
cv2.waitKey(0)
cv2.destroyAllWindows()
