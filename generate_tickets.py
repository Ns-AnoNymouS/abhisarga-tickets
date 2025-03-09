import os
import time
import random

import cv2
import dotenv
import qrcode
import numpy as np
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont

dotenv.load_dotenv()


def connect_database():
    """
    Establishes a connection to the MongoDB database.

    Returns:
        Database object for interacting with MongoDB collections.
    """
    print("Connecting to Database...")
    database_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    client = MongoClient(database_url)
    db = client["abhisarga"]
    print("Database Connected")
    return db


db = connect_database()
users_collection = db["users"]
tickets_collection = db["tickets"]


def overlay_image(
    background_path: str, overlay_path: str, x: int, y: int, height: int
) -> np.ndarray:
    """
    Overlays an image onto a background at a specified position while maintaining its aspect ratio.

    Args:
        background_path (str): Path to the background image.
        overlay_path (str): Path to the image to overlay.
        x (int): X-coordinate for overlay placement.
        y (int): Y-coordinate for overlay placement.
        height (int): Desired height of the overlay image.

    Returns:
        np.ndarray: Image with the overlay applied.
    """
    background = cv2.imread(background_path)
    overlay = cv2.imread(overlay_path)

    bg_h, bg_w, _ = background.shape
    ol_h, ol_w, _ = overlay.shape

    # Maintain aspect ratio while resizing
    aspect_ratio = ol_w / ol_h
    new_width = int(height * aspect_ratio)
    overlay_resized = cv2.resize(overlay, (new_width, height))

    ol_h, ol_w, _ = overlay_resized.shape
    if x + ol_w > bg_w:
        ol_w = bg_w - x
        overlay_resized = overlay_resized[:, :ol_w]
    if y + ol_h > bg_h:
        ol_h = bg_h - y
        overlay_resized = overlay_resized[:ol_h, :]

    # Create masks to blend overlay onto background
    overlay_gray = cv2.cvtColor(overlay_resized, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(overlay_gray, 1, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    bg_roi = background[y : y + ol_h, x : x + ol_w]
    bg_with_mask = cv2.bitwise_and(bg_roi, bg_roi, mask=mask_inv)
    overlay_with_mask = cv2.bitwise_and(overlay_resized, overlay_resized, mask=mask)

    background[y : y + ol_h, x : x + ol_w] = cv2.add(bg_with_mask, overlay_with_mask)
    return background


def add_rotated_text(
    image: np.ndarray,
    text: str,
    position: tuple,
    font_path: str,
    font_size: int,
    angle: int = 90,
    color: tuple = (0, 0, 0),
) -> np.ndarray:
    """
    Adds rotated text to an image without cropping it.

    Args:
        image (np.ndarray): The image to add text to.
        text (str): The text to overlay.
        position (tuple): (x, y) position of text center.
        font_path (str): Path to the font file.
        font_size (int): Font size.
        angle (int, optional): Rotation angle (default: 90 degrees).
        color (tuple, optional): Text color in (R, G, B) format (default: black).

    Returns:
        np.ndarray: Image with the rotated text added.
    """
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    font = ImageFont.truetype(font_path, font_size)

    # Measure text size
    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw_dummy = ImageDraw.Draw(dummy_img)
    text_w, text_h = draw_dummy.textbbox((0, 0), text, font=font)[2:]

    # Create a canvas to hold rotated text
    canvas_size = (int(text_w * 1.5), int(text_h * 1.5))
    text_image = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw_text = ImageDraw.Draw(text_image)
    text_position = ((canvas_size[0] - text_w) // 2, (canvas_size[1] - text_h) // 2)
    draw_text.text(text_position, text, font=font, fill=color + (255,))

    rotated_text = text_image.rotate(angle, expand=True)
    paste_x = position[0] - rotated_text.width // 2
    paste_y = position[1] - rotated_text.height // 2
    image_pil.paste(rotated_text, (paste_x, paste_y), rotated_text)
    return cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)


def generate_qr(text: str, filename: str = "qrcode.png") -> None:
    """Generates and saves a QR code from the provided text."""
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


def generate_final_ticket() -> None:
    """
    Generates a unique ticket with a QR code, overlays it on a background image,
    and saves the final ticket image to disk while storing ticket details in the database.
    """
    unique_id = f"AB{random.randint(1000, 9999)}{int(time.time() * 1000)}"
    print(f"Generating Ticket: {unique_id}")

    generate_qr(unique_id)
    output = overlay_image(
        "ticket_template.png", "qrcode.png", x=186, y=394, height=182
    )

    # Add rotated ticket number text
    output = add_rotated_text(
        image=output,
        text=f"Ticket No: {unique_id}",
        position=(395, 490),
        font_path="Poppins-Medium.ttf",
        font_size=13,
        angle=90,
        color=(0, 0, 0),
    )

    os.makedirs("tickets", exist_ok=True)
    ticket_path = os.path.join("tickets", f"{unique_id}.png")
    cv2.imwrite(ticket_path, output)
    tickets_collection.insert_one({"ticket": unique_id})


def generate_bulk_tickets(count: int = 500) -> None:
    """Generates multiple tickets in bulk based on the specified count."""
    for i in range(count):
        generate_final_ticket()
        print(f"{i+1}/{count} Tickets Generated")
    print("Tickets Generated Successfully")


def main() -> None:
    """Main function to prompt the user for the number of tickets to generate."""
    try:
        count = int(input("Enter the number of tickets to generate: "))
        if count <= 0:
            print("Please enter a valid positive number.")
        else:
            generate_bulk_tickets(count)
    except ValueError:
        print("Invalid input. Please enter a numeric value.")


if __name__ == "__main__":
    main()
