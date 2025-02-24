from picoed import display

# Funkce pro nastavení pixelu
def set_pixel(x, y, brightness):
    display.pixel(x, y, brightness)

# Příklad použití funkce
set_pixel(0, 0, 255)  # Nastaví pixel na pozici (2, 2) s jasem 9
