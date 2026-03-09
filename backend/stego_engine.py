from PIL import Image


def text_to_binary(text):
    return ''.join(format(ord(i), '08b') for i in text)


def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    message = ''.join(chr(int(c, 2)) for c in chars)
    return message


def hide_message(image, secret_message):

    
    secret_message += "#####"

    binary_secret = text_to_binary(secret_message)

    img = image.convert("RGB")
    pixels = list(img.getdata())

    new_pixels = []
    data_index = 0

    for pixel in pixels:
        r, g, b = pixel

        if data_index < len(binary_secret):
            r = (r & ~1) | int(binary_secret[data_index])
            data_index += 1

        if data_index < len(binary_secret):
            g = (g & ~1) | int(binary_secret[data_index])
            data_index += 1

        if data_index < len(binary_secret):
            b = (b & ~1) | int(binary_secret[data_index])
            data_index += 1

        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    return img


def extract_message(image):

    img = image.convert("RGB")
    pixels = list(img.getdata())

    binary_data = ""

    for pixel in pixels:
        r, g, b = pixel

        binary_data += str(r & 1)
        binary_data += str(g & 1)
        binary_data += str(b & 1)

    all_bytes = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]

    decoded_message = ""

    for byte in all_bytes:
        decoded_message += chr(int(byte, 2))

        if decoded_message.endswith("#####"):
            return decoded_message[:-5]

    return "No hidden message found"