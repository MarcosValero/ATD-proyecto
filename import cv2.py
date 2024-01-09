import cv2
from pyzbar.pyzbar import decode
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def descarte_marcas_blancas(texto, marca):
        d_marcas_blancas = {'mercadona':'hacendado','carrefour':'carrefour','consum':'consum',
                            'el corte inglés':'el corte inglés','dia':'dia'}
        if marca in d_marcas_blancas:
            marca_blanca = d_marcas_blancas[marca]
            coincidencia = re.compile(fr'\b{marca_blanca}\b',re.IGNORECASE)
            if coincidencia.search(texto):
                return True
        return False

def read_barcodes(frame):
    barcodes = decode(frame)
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        x, y, w, h = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Mostrar información del código de barras
        text = f"{barcode_data} ({barcode_type})"
        print("[INFO] Encontrado {} código: {}".format(barcode_data, barcode_type))
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        if barcode_data is not None:
            return (barcode_data,True)
    return (None,False)

def generar_tabla(lista):
    df = pd.DataFrame('---',columns= lista ,index='nombre_producto precio precio_unitario'.split())
    return df

def realizar_consulta(codigo):
    url = f"https://go-upc.com/search?q={codigo}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text,'html.parser')
            return soup
        else:
            print(f"Error en la solicitud. Código de error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")

def main():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar el cuadro")
            break

        numero,barcode_detected = read_barcodes(frame)
        cv2.imshow('Barcode Scanner', frame)

        if barcode_detected:
            break

        if cv2.waitKey(1) & 0xFF == 27:  # Presiona Esc para salir
            break
    soup = realizar_consulta(numero)
    clase = soup.find('h1', class_='product-name')
    etiqueta_brand = soup.find('td',class_='metadata-label',string=re.compile(r'brand',re.IGNORECASE))
    if etiqueta_brand:
        brand = (etiqueta_brand.find_next_sibling('td')).get_text(strip=True) + ' '
    if clase:
        producto = clase.text
        prefijo = 0
        for c_np, c_b in zip(producto, brand):
            if c_np == c_b:
                prefijo += 1
            else:
                break
        nombre_producto = producto[prefijo:]
    else:
        raise IndexError('No se encuentra el elemento escaneado')
    lista_super = ['mercadona','carrefour','consum','el corte inglés','dia']
    for super in lista_super:
        if descarte_marcas_blancas(producto, super):
            pass
    generar_tabla(lista_super)
    print(f'{brand}: {nombre_producto}')
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
