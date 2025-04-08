# Muazzin - the one who recites azan

## Introduction

This app will play _azan_ when prayer time comes.<br>
Prayer time is downloaded as `rss feed` from [Portal e-Solat](https://www.e-solat.gov.my/).<br>
I actually wish to hear _azan_ on every prayer times as it gives me peace and a better sense of time-awareness.<br>
This app uses the power of `Docker Engine` and can run on any device that runs Docker.

## Notes

1. This  app is uses `rss feed` from [Portal e-Solat](https://www.e-solat.gov.my/) website.
2. Docker installation: Visit [Docker website](https://docs.docker.com/get-docker/)

## Installation

1. Build docker image using provided `Dockerfile`.
    ```
    docker build -t muazzin .
    ```
1. Run the docker in persistence.
    ```
    docker run \
        --detach \
        --restart unless-stopped \
        --device /dev/snd \
        --volume $(pwd)/userspace:/home/muazzin/userspace \
        muazzin
    ```
1. New folder `userspace` will be created for you with default `config.toml` and `azan.m4a` file. You may change these file as you like.
    ```
    # config.toml

    [Settings]
    KodKawasan = "PHG03"
    AzanFile = "azan.m4a"
    YearlyAzanCsvFile = "jadual_waktu_solat_JAKIM_2025.csv"
    
    [Telegram]
    BotToken = ""  # Replace with your actual bot token
    ChatId = ""  # Replace with your actual user id
    ```
1. Attach speaker (or laudspeaker if you want) and just keep your server/raspberry pi/computer running.

## Kod Kawasan

| Negeri          | Kod     | Kawasan    |
| :----:          | :-----: | :--------- |
| Johor           | JHR01   | Pulau Aur dan Pulau Pemanggil  |
| Johor           | JHR02   | Johor Bahru, Kota Tinggi, Mersing |
| Johor           | JHR03   | Kluang, Pontian |
| Johor           | JHR04   | Batu Pahat, Muar, Segamat, Gemas Johor |
| Kedah           | KDH01   | Kota Setar, Kubang Pasu, Pokok Sena (Daerah Kecil) |
| Kedah           | KDH02   | Kuala Muda, Yan, Pendang |
| Kedah           | KDH03   | Padang Terap, Sik |
| Kedah           | KDH04   | Baling |
| Kedah           | KDH05   | Bandar Baharu, Kulim |
| Kedah           | KDH06   | Langkawi |
| Kedah           | KDH07   | Puncak Gunung Jerai |
| Kelantan        | KTN01   | Bachok, Kota Bharu, Machang, Pasir Mas, Pasir Puteh, Tanah Merah, Tumpat, Kuala Krai, Mukim Chiku |
| Kelantan        | KTN03   | Gua Musang (Daerah Galas Dan Bertam), Jeli, Jajahan Kecil Lojing |
| Melaka          | MLK01   | SELURUH NEGERI MELAKA |
| Negeri Sembilan | NGS01   | Tampin, Jempol |
| Negeri Sembilan | NGS02   | Jelebu, Kuala Pilah, Port Dickson, Rembau, Seremban |
| Pahang          | PHG01   | Pulau Tioman |
| Pahang          | PHG02   | Kuantan, Pekan, Rompin, Muadzam Shah |
| Pahang          | PHG03   | Jerantut, Temerloh, Maran, Bera, Chenor, Jengka |
| Pahang          | PHG04   | Bentong, Lipis, Raub |
| Pahang          | PHG05   | Genting Sempah, Janda Baik, Bukit Tinggi |
| Pahang          | PHG06   | Cameron Highlands, Genting Higlands, Bukit Fraser |
| Perlis          | PLS01   | Kangar, Padang Besar, Arau |
| Pulau Pinang    | PNG01   | Seluruh Negeri Pulau Pinang |
| Perak           | PRK01   | Tapah, Slim River, Tanjung Malim |
| Perak           | PRK02   | Kuala Kangsar, Sg. Siput , Ipoh, Batu Gajah, Kampar |
| Perak           | PRK03   | Lenggong, Pengkalan Hulu, Grik |
| Perak           | PRK04   | Temengor, Belum |
| Perak           | PRK05   | Kg Gajah, Teluk Intan, Bagan Datuk, Seri Iskandar, Beruas, Parit, Lumut, Sitiawan, Pulau Pangkor |
| Perak           | PRK06   | Selama, Taiping, Bagan Serai, Parit Buntar |
| Perak           | PRK07   | Bukit Larut |
| Sabah           | SBH01   | Bahagian Sandakan (Timur), Bukit Garam, Semawang, Temanggong, Tambisan, Bandar Sandakan, Sukau |
| Sabah           | SBH02   | Beluran, Telupid, Pinangah, Terusan, Kuamut, Bahagian Sandakan (Barat) |
| Sabah           | SBH03   | Lahad Datu, Silabukan, Kunak, Sahabat, Semporna, Tungku, Bahagian Tawau  (Timur) |
| Sabah           | SBH04   | Bandar Tawau, Balong, Merotai, Kalabakan, Bahagian Tawau (Barat) |
| Sabah           | SBH05   | Kudat, Kota Marudu, Pitas, Pulau Banggi, Bahagian Kudat |
| Sabah           | SBH06   | Gunung Kinabalu |
| Sabah           | SBH07   | Kota Kinabalu, Ranau, Kota Belud, Tuaran, Penampang, Papar, Putatan, Bahagian Pantai Barat |
| Sabah           | SBH08   | Pensiangan, Keningau, Tambunan, Nabawan, Bahagian Pendalaman (Atas) |
| Sabah           | SBH09   | Beaufort, Kuala Penyu, Sipitang, Tenom, Long Pa Sia, Membakut, Weston, Bahagian Pendalaman (Bawah) |
| Selangor        | SGR01   | Gombak, Petaling, Sepang, Hulu Langat, Hulu Selangor, S.Alam |
| Selangor        | SGR02   | Kuala Selangor, Sabak Bernam |
| Selangor        | SGR03   | Klang, Kuala Langat |
| Sarawak         | SWK01   | Limbang, Lawas, Sundar, Trusan |
| Sarawak         | SWK02   | Miri, Niah, Bekenu, Sibuti, Marudi |
| Sarawak         | SWK03   | Pandan, Belaga, Suai, Tatau, Sebauh, Bintulu |
| Sarawak         | SWK04   | Sibu, Mukah, Dalat, Song, Igan, Oya, Balingian, Kanowit, Kapit |
| Sarawak         | SWK05   | Sarikei, Matu, Julau, Rajang, Daro, Bintangor, Belawai |
| Sarawak         | SWK06   | Lubok Antu, Sri Aman, Roban, Debak, Kabong, Lingga, Engkelili, Betong, Spaoh, Pusa, Saratok |
| Sarawak         | SWK07   | Serian, Simunjan, Samarahan, Sebuyau, Meludam |
| Sarawak         | SWK08   | Kuching, Bau, Lundu, Sematan |
| Sarawak         | SWK09   | Zon Khas (Kampung Patarikan) |
| Terengganu      | TRG01   | Kuala Terengganu, Marang, Kuala Nerus |
| Terengganu      | TRG02   | Besut, Setiu |
| Terengganu      | TRG03   | Hulu Terengganu |
| Terengganu      | TRG04   | Dungun, Kemaman |
| Wilayah Persekutuan | WLY01 | Kuala Lumpur, Putrajaya |
| Wilayah Persekutuan | WLY02 | Labuan |
