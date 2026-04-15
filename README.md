# Socket Server-Client Project

## Përshkrimi

Ky projekt implementon një server dhe klient duke përdorur TCP sockets në Python. Serveri menaxhon shumë klientë, ruan mesazhe dhe lejon operacione mbi file.

Gjithashtu, serveri përfshin një HTTP server për monitorim në endpoint:
http://localhost:8080/stats

---

## Funksionalitetet

* Multi-client server (threading)
* Role: ADMIN dhe USER
* Timeout për klientët jo aktivë
* Operacione me file (upload, download, delete, read)
* HTTP server për statistika

---

## Komandat

* /list
* /read <filename>
* /search <keyword>
* /download <filename>

ADMIN:

* /upload <filename>
* /delete <filename>
* /info <filename>

---

## Ekzekutimi

Server:
python server.py

Klient:
python client.py

