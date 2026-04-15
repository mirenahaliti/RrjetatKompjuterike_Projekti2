# UDP Client-Server Application 

##  Përshkrimi

Ky projekt është zhvilluar në kuadër të lëndës **Rrjeta Kompjuterike** dhe implementon një sistem komunikimi **Client-Server duke përdorur protokollin UDP në Python**.

Serveri mundëson komunikimin me shumë klientë njëkohësisht në një rrjet real dhe ofron funksionalitete për menaxhimin e file-ve, monitorimin e aktivitetit dhe kontrollin e aksesit.

---

##  Teknologjitë e përdorura

* **Python**
* **UDP (User Datagram Protocol)**
* **Socket Programming**
* **Threading (për HTTP server dhe timeout monitoring)**

---


##  Funksionalitetet

###  Serveri

* Pranon mesazhe nga shumë klientë në të njëjtën kohë
* Identifikon klientët përmes adresës (IP, port)
* Klienti i parë bëhet **ADMIN**, të tjerët janë **USER**
* Ruan statistika për:

  * klientët aktivë
  * numrin total të mesazheve
* Implementon **timeout (60 sekonda)** për klientët joaktivë
* Kufizon numrin e klientëve (MAX_CLIENTS = 4)
* Ofron operacione mbi file në server

---

###  Klienti

* Dërgon komanda në server
* Merr përgjigje nga serveri
* Mbështet:

  * dërgim mesazhesh
  * upload file
  * download file

---

##  Komandat

### Komandat për të gjithë klientët

* `/list` – liston file-at në server
* `/read <filename>` – lexon përmbajtjen e file-it
* `/search <keyword>` – kërkon file sipas emrit
* `/download <filename>` – shkarkon file nga serveri

### Komandat vetëm për ADMIN

* `/upload <filename>` – ngarkon file në server
* `/delete <filename>` – fshin file nga serveri
* `/info <filename>` – shfaq informacione mbi file

---

##  HTTP Monitorimi

Serveri përfshin një HTTP server që funksionon paralelisht në portin **8080**.

### Endpoint:

```id="h5f7kl"
GET /stats
```

### Kthen:

* listën e klientëve aktivë
* numrin total të mesazheve

---

##  Ekzekutimi

### 1. Starto serverin

```bash id="q1x8nz"
python server.py
```

### 2. Starto klientët (në të paktën 4 pajisje)

```bash id="z8k2vn"
python client.py
```

---

##  Konfigurimi i rrjetit

* Pajisjet duhet të jenë në të njëjtin rrjet (WiFi/LAN)
* Klienti duhet të përdorë IP adresën e serverit
* Duhet të lejohen komunikimet UDP në firewall

---



