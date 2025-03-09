# 🎟️ Abhisarga 25 - Automated Ticket Generation & Verification

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)  
![MongoDB](https://img.shields.io/badge/MongoDB-%2334A853.svg?style=flat-square&logo=mongodb&logoColor=white)   
![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-orange?style=flat-square)  

This project automates ticket generation for **Abhisarga 25**, eliminating the need for manually writing ticket numbers and names. It generates **QR-coded tickets**, allows **web-based verification**, and securely stores ticket data in **MongoDB**.

## ✨ Features  
✅ **Automated Ticket Generation** – Unique tickets with QR codes  
✅ **Web-based Authentication** – Secure login for authorized users  
✅ **QR Code Scanning** – Verify ticket details instantly  
✅ **Real-time Ticket Assignment** – Register buyer details dynamically  
✅ **Persistent Storage** – All data securely stored in MongoDB  

## 🛠️ Setup Instructions  

### 📌 1. Install Dependencies  
Ensure **Python 3.8+** is installed. Then, run:  
```sh
pip install -r requirements.txt
```

### 🔑 2. Configure Environment Variables  
Create a `.env` file in the root directory and add:  
```sh
DATABASE_URL=<your_mongodb_url>
JWT_SECRET_KEY=<your_secret_key>
ADMIN_USERNAME=<your_admin_username>
ADMIN_PASSWORD=<your_admin_password>
```
- `DATABASE_URL`: MongoDB connection string.  
- `JWT_SECRET_KEY`: Secret key for authentication.  
- `ADMIN_USERNAME`: Admin username for user management.  
- `ADMIN_PASSWORD`: Admin password for user management.  

### 🌟 3. Create New Users  
To create a new user, make a **POST request** to `/user` with **JSON data** in the following format:
```json
{
    "admin_username": "<your_admin_username>",
    "admin_password": "<your_admin_password>",
    "new_username": "<new_user_username>",
    "new_password": "<new_user_password>"
}
```
If the provided admin credentials are correct, a new user will be created, and a JWT token will be returned.

### 🌟 4. Generate Tickets  
Update `ticket_template.png` as needed. Adjust QR code and ticket number positions:  

```python
output = overlay_image(
    "ticket_template.png", "qrcode.png", x=186, y=394, height=182
)
```
- **(x, y)** → QR code position.  
- **height** → QR code size.  

Modify ticket number text properties:  
```python
output = add_rotated_text(
    image=output,
    text=f"Ticket No: {unique_id}",
    position=(395, 490),
    font_path="Poppins-Medium.ttf",
    font_size=13,
    angle=90,
    color=(0, 0, 0),
)
```
- **position (x, y)** → Ticket number placement.  
- **angle** → Text rotation.  
- **color, font_size** → Custom styling.  

Run the script:  
```sh
python generate_tickets.py
```
Enter the number of tickets to generate. Generated tickets are saved in the **`tickets/`** folder.

### 🌐 5. Run the Web Server  
Start the server using:  
```sh
python server.py
```
This launches the **web-based ticket verification system**.

## 🎯 How It Works  
- **Login** – Authorized users sign in.  
- **Scan QR Code** – If unassigned, register buyer details.  
- **Re-Scan** – View ticket holder’s details.  

## 🤝 Contribution  
We welcome contributions!  
Fork the repo, make your changes, and submit a **pull request**!  

💙 **Star this repository if you found it useful!** ⭐

