from django.shortcuts import render, redirect, get_object_or_404
from utils import *
from django.http import JsonResponse
import json
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from authentication.forms import *
from django.contrib.auth import get_user_model
from django.contrib import messages
from authentication.models import *
from .models import *
import os
from django.conf import settings
import csv

import pandas as pd
import re
import pytesseract
from PIL import Image
from datetime import datetime
from django.db import IntegrityError

# Sample phishing keywords
PHISHING_KEYWORDS = [
        "immediate action required", "act now", "response needed", "attention required",
        "confirm now", "validate your account", "suspicious activity", "limited time",
        "final notice", "take action", "click now", "account suspended", "account locked",
        "unusual login attempt", "update your information", "security alert",
        "password expired", "login required", "identity verification",
        "two-factor authentication required", "bank notice", "transaction failed",
        "payment required", "invoice attached", "you have won", "claim your reward",
        "refund available", "billing issue", "credit card declined", "earn money fast",
        "from admin", "it support", "helpdesk", "system administrator",
        "microsoft support", "apple id", "amazon security", "paypal alert",
        "click here", "login to your account", "secure link", "update now",
        "open attachment", "check your statement", "reset your password", "access here",
        "reactivate", "verify your account", "urgent", "suspended", "login", "bank",
        "password", "confirm", "tuma kwenye", "Nipigie baada ya saa moja, tafadhali",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA","KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA",
        "Naomba unitumie iyo Hela kwenye namba hii ya Airtel . jina ()",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0615810764 AU 0615810764",
        "IYO PESA ITUME KWENYE NAMBA HII 0657538690 JINA ITALETA Magomba Maila NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Iyo pesa itume humu kwenye AIRTEL 0696530433 jina lije OLIVA MATIAS.",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By RAMATUNGU,ni grp member",
        "We need urgently Need Staff salary 4,000,000TZS. Reach HR team at: wa.me/2550657538690.",
        "0755896103 Jina litakuja SALOME KALUNGA Nitumie kwenye hiyo ",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0676584303 UKIWA TAYARI KUJIUNGA",
        "Utanitumia kwa hîi   j'ina ni .",
        "Congratulations! Your CV has passed. You can get 170,000TZS in a day. for details: wa.me/255",
        "Tuzo point hongera umepata zawadi Sh170,000 milioni kutoka (Tuzo point) piga sim,.0617488472 kupata zawadi  asante",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By SALOME KALUNGA,ni grp member",
        "Nitumie tu kwenye hii voda 0699137921 jina JUMANNE YASINI MASAKA.",
        "Hela tuma kwa namba hii 0655251448 jina LINUSI MALALO",
        "Utanitumia kwa hîi  0657666983 j'ina ni ABDALLAH MWANAKU.",
        " CQGZ Imethibitishwa namba yako ya 078 ... imeshinda Tsh10,000,000.00/=million kutoka TUZO  POINTI ilikupokea Hela yako piga 0787-406-889 Asante",
        "au iyo ela nitumie kwenye M-Pesa hii 0676584303 Jina litoke 0676584303.",
        "Samahani naomba itume kwenye  0654321098 ABDALLAH MWANAKU.",
        "Utanitumia. kwemye namba 0784862618 ya airtel jina HOSEA MKUMBUKWA.",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0781476081 au 0781476081",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "MPIGIE MZEE RAMATUNGU WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0747878264",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA Halotel NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        " Jina litakuja  Nitumie kwenye hiyo Halotel",
        "0755896103 Jina litakuja  Nitumie kwenye hiyo voda",
        "Utanitumia kwenye ii 0615810764  jina  namba yangu inadeni usiitumie",
        "Mpigie Mzee LINUSI MALALO kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0657538690",
        "Iyo ela tuma humu kwenye  0689592818 Jina lije Magomba Maila.",
        "Au nitumie kwenye HaloPesa Namba.0786543210 jina litakuja SALOME KALUNGA",
        "Utanitumia kwenye ii 0615810764 airtel jina MARIAM NDUGAI namba yangu inadeni usiitumie",
        "Iyo Hela itume humu kwenye HALOTEL 0787-406-889 jina lije ABDALLAH MWANAKU.",
        "IYO PESA ITUME KWENYE NAMBA HII 0786543210 JINA ITALETA RAMATUNGU NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0782435667)(0782435667)",
        "Iyo Pesa itume humu kwenye  0747878264 jina lije .",
        "Iyo Pesa itume humu kwenye  0698018072 jina lije HOSEA MKUMBUKWA.",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "Imethibitishwa, namba yako ya 0733822240 imejishindia TSH 1,500,000 kutoka TUZO  POINTI. Piga 0733822240 ili kupokea Pesa yako.",
        "Utanitumia kwa hîi   j'ina ni Magomba Maila.",
        "Iyo Pesa itume humu kwenye Airtel  jina lije JENEROZA ROCK BENEDICTO.",
        "Mpigie Mzee MARIAM NDUGAI kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga ",
        ", No need to go out work, just at home to earn 4,000,000TZS a day, please contact us: https://wa.me/255",
        "Imethibitishwa, namba yako ya 0657538690 imejishindia TSH 5,000,000 kutoka TUZO  POINTI. Piga 0657538690 ili kupokea hela yako.",
        "ela tuma kwa namba hii 0788542784 jina RAMATUNGU",
        "TUMIA NAMBA HII ()KUNITUMIA IYO HELA JINA LITAONYESHA (MARIAM NDUGAI)",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0786543210 AU 0786543210",
        "Mpigie Mzee MARIAM NDUGAI kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga ",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By PEREGIA FILIPO,ni grp member",
        "Congratulations! Your CV has passed. You can get 2,000,000TZS in a day. for details: wa.me/255",
        "halotel PSK4 Imethibitishwa namba yako ya 065 ... imeshinda Tsh4,000,000.00/=million kutoka Tuzo Point ilikupokea ela yako piga 0696530433 Asante",
        "tuma kwenye namba hii ya HaloPesa 0695567435 jina litakuja JUMANNE YASINI MASAKA Ukituma unijulishe",
        "Mpigie Mzee JUMANNE YASINI MASAKA kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0657538690",
        "Iyo ela tuma humu kwenye  0655251448 Jina lije ",
        "We need urgently Need Staff salary 120000TZS. Reach HR team at: wa.me/255.",
        " 0E7D Imethibitishwa namba yako ya 061 ... imeshinda Tsh2,000,000.00/=million kutoka VODA OFA ilikupokea ela yako piga 0615810764 Asante",
        "Iyo Hela itume humu kwenye  0696530433 jina lije .",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0676584303 au 0676584303",
        "Basi iyo hela nitumie kwenye namba hii 0615810764 jina litakuja () ile namba usitumie laini inamatatizo.",
        "IYO PESA ITUME KWENYE NAMBA HII 0698018072 JINA ITALETA LINUSI MALALO NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "MZEE SALOME KALUNGA tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0733822240)(0733822240)",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "tuma kwenye namba hii ya m-pesa 0755896103 jina litakuja RAMATUNGU Ukituma unijulishe",
        "Iyo ela tuma humu kwenye HALOTEL 0781476081 Jina lije JUMANNE YASINI MASAKA",
        ", No need to go out work, just at home to earn 4,000,000TZS a day, please contact us: https://wa.me/2550676584303",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Utanitumia. kwemye namba 0689592818 ya  jina .",
        "VODA OFA hongera umepata zawadi Sh10,000,000 milioni kutoka (VODA OFA) piga sim,.0781476081 kupata zawadi  asante",
        "Nitumie tu kwenye hii  0782734560 jina .",
        "Iyo ela tuma humu kwenye  0755896103 Jina lije ",
        "Habari za mchana,mimi LINUSI MALALO,hii namba yangu ya .Vp mbona shem LINUSI MALALO, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "TUMIA NAMBA HII (0657666983)KUNITUMIA IYO HELA JINA LITAONYESHA (MWANAIDI KHAMISI)",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Naomba unitumie iyo ela kwenye namba hii ya  0781476081. jina ()",
        "Au nitumie kwenye AirtelMoney Namba. jina litakuja JENEROZA ROCK BENEDICTO",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Habari za siku. Mimi  mwenye nyumba wako hii namba yangu ya halotel. Mbona kimya na siku zinazidi kwenda...?",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0788542784 au 0788542784",
        "Congratulations! Your CV has passed. You can get 6,000,000TZS in a day. for details: wa.me/2550786543210",
        "Mpigie Mzee Magomba Maila kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0782734560",
        "TUMIA NAMBA HII (0782734560)KUNITUMIA IYO HELA JINA LITAONYESHA (Ester kalobelo)",
        "IYO PESA ITUME KWENYE NAMBA HII 0733822240 JINA ITALETA NASHONI MBIRIBI NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0755896103 au 0755896103",
        "Mpigie Mzee FEBU SHADI WILISON kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga ",
        "Nitumie tu kwenye hii Halotel  jina .",
        "Congratulations! Your CV has passed. You can get 6,000,000TZS in a day. for details: wa.me/2550657538690",
        "Naomba unitumie iyo ela kwenye namba hii ya voda 0695567435. jina ()",
        "0782734560 Jina litakuja  Nitumie kwenye hiyo ",
        "Iyo ela tuma humu kwenye airtel 0695567435 Jina lije OLIVA MATIAS.",
        ", No need to go out work, just at home to earn 2,000,000TZS a day, please contact us: https://wa.me/2550755667788",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0787-406-889)(0787-406-889)",
        ", No need to go out work, just at home to earn 1,500,000TZS a day, please contact us: https://wa.me/2550699137921",
        "0786543210 Jina litakuja  Nitumie kwenye hiyo ",
        "mjukuu wangu utafuta ji wako mgumu Pesa hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. ",
        "Iyo ela tuma humu kwenye  0657538690 Jina lije JUMANNE YASINI MASAKA.",
        "Utanitumia. kwemye namba 0788542784 ya  jina FEBU SHADI WILISON.",
        "Naomba unitumie iyo Pesa kwenye namba hii ya Halotel 0755667788. jina (RAMATUNGU)",
        "Tumia namba hii ya voda 0695567435 kutuma hiyo Pesa jina ",
        "We need urgently Need Staff salary 6,000,000TZS. Reach HR team at: wa.me/2550773409724.",
        "MPIGIE MZEE HOSEA MKUMBUKWA WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0781476081",
        "Mpigie Mzee MWANAIDI KHAMISI kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0654321098"
        "Iyo ela tuma humu kwenye halotel 0781476081 Jina lije ABDALLAH MWANAKU.",
        "Congratulations! Your CV has passed. You can get 170,000TZS in a day. for details: wa.me/2550786543210",
        "mjukuu wangu utafuta ji wako mgumu ela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0716484506",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya HALOTEL. Mbona kimya na siku zinazidi kwenda...?",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0733822240 UKIWA TAYARI KUJIUNGA",
        "Habari za siku,mimi OLIVA MATIAS,hii namba yangu ya .Vp mbona shem OLIVA MATIAS, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "Iyo ela itume humu kwenye HALOTEL 0695567435 jina lije PEREGIA FILIPO.",
        "mjukuu wangu utafuta ji wako mgumu ela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0657666983",
        "tuma kwenye namba hii ya m-pesa 0617488472 jina litakuja  Ukituma unijulishe",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA ",
        "Samahani naomba itume kwenye AIRTEL 0733822240 .",
        "Utanitumia. kwemye namba 0696530433 ya airtel jina OLIVA MATIAS.",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0784862618 au 0784862618",
        "Iyo ela tuma humu kwenye halotel  Jina lije ",
        "Habari. Mimi  mwenye nyumba wako hii namba yangu ya HALOTEL. Mbona kimya na siku zinazidi kwenda...?",
        "Iyo Hela itume humu kwenye halotel 0615810764 jina lije OLIVA MATIAS.",
        ", No need to go out work, just at home to earn 170,000TZS a day, please contact us: https://wa.me/2550786543210",
        "Habari za mda huu,mimi Magomba Maila,hii namba yangu ya .Vp mbona shem Magomba Maila, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "Utanitumia kwenye ii  airtel jina  namba yangu inadeni usiitumie",
        "Habari za siku,mimi SALOME KALUNGA,hii namba yangu ya AIRTEL.Vp mbona shem SALOME KALUNGA, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "Habari,mimi LINUSI MALALO,hii namba yangu ya Halotel.Vp mbona shem LINUSI MALALO, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA AIRTEL NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0716484506",
        "Tumia namba hii ya Airtel 0786543210 kutuma hiyo ela jina Magomba Maila",
        "Samahani naomba itume kwenye   .",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Iyo Pesa itume humu kwenye airtel 0654321098 jina lije MWANAIDI KHAMISI.",
        "Utanitumia kwa hîi   j'ina ni .",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0657538690",

        "We need urgently Need Staff salary 4,000,000TZS. Reach HR team at: wa.me/2550782435667.",
        "Samahani naomba itume kwenye voda 0689592818 .",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "TUMIA NAMBA HII ()KUNITUMIA IYO HELA JINA LITAONYESHA (RAMATUNGU)",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By JUMANNE YASINI MASAKA,ni grp member",
        "au iyo ela nitumie kwenye HaloPesa hii  Jina litoke .",

        "pesa tuma kwa namba hii  jina ",

        "Iyo ela tuma humu kwenye  0698018072 Jina lije JENEROZA ROCK BENEDICTO.",

        "0782435667 Jina litakuja MWANAIDI KHAMISI Nitumie kwenye hiyo Airtel",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0615810764",
        "Pesa tuma kwa namba hii  jina ",
        "au iyo ela nitumie kwenye AirtelMoney hii 0787-406-889 Jina litoke 0787-406-889.",
        "Iyo ela tuma humu kwenye airtel 0695567435 Jina lije LINUSI MALALO",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0755667788 au 0755667788",
        " RJSR Imethibitishwa namba yako ya 078 ... imeshinda Tsh120000.00/=million kutoka TUZO POINT ilikupokea pesa yako piga 0698018072 Asante",

        "Utanitumia kwa hîi halotel  j'ina ni .",

        "Mpigie Mzee JUMANNE YASINI MASAKA kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0615810764",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0699137921 UKIWA TAYARI KUJIUNGA",
        "Iyo hela itume humu kwenye  0747878264 jina lije SALOME KALUNGA.",
        "Naomba unitumie iyo ela kwenye namba hii ya airtel 0617488472. jina ()",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By PEREGIA FILIPO,ni grp member",

        "IYO PESA ITUME KWENYE NAMBA HII 0750335946 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "MZEE LINUSI MALALO tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0782734560)(0782734560)",
        "IYO PESA ITUME KWENYE NAMBA HII 0716484506 JINA ITALETA PEREGIA FILIPO NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "TUMIA NAMBA HII (0781476081)KUNITUMIA IYO HELA JINA LITAONYESHA ()",

        "TUZO POINT hongera umepata zawadi Sh1,500,000 milioni kutoka (TUZO POINT) piga sim,.0781476081 kupata zawadi  asante",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "tuma kwenye namba hii ya M-Pesa  jina litakuja FEBU SHADI WILISON Ukituma unijulishe",
        "Mpigie Mzee LINUSI MALALO kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0695567435",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0747878264 AU 0747878264",

        ", No need to go out work, just at home to earn 170,000TZS a day, please contact us: https://wa.me/2550655251448",
        "Utanitumia kwenye ii 0773409724 airtel jina  namba yangu inadeni usiitumie",
        "0786543210 Jina litakuja  Nitumie kwenye hiyo ",
        "mjukuu wangu utafuta ji wako mgumu hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0782734560",

        "Au nitumie kwenye m-pesa Namba. jina litakuja ",
        "Iyo ela tuma humu kwenye voda  Jina lije JENEROZA ROCK BENEDICTO",
        "Tumia namba hii ya airtel 0787-406-889 kutuma hiyo Hela jina HOSEA MKUMBUKWA",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya Halotel. Mbona kimya na siku zinazidi kwenda...?",
        ", No need to go out work, just at home to earn 170,000TZS a day, please contact us: https://wa.me/2550755896103",
        "Basi iyo hela nitumie kwenye namba hii  jina litakuja (PEREGIA FILIPO) ile namba usitumie laini inamatatizo.",

        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Iyo Hela itume humu kwenye  0698018072 jina lije .",
        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "Naomba unitumie iyo Hela kwenye namba hii ya  . jina (PEREGIA FILIPO)",
        "We need urgently Need Staff salary 5,000,000TZS. Reach HR team at: wa.me/2550755667788.",
        "Iyo Pesa itume humu kwenye Halotel 0755667788 jina lije PEREGIA FILIPO.",
        "Basi iyo hela nitumie kwenye namba hii 0698018072 jina litakuja () ile namba usitumie laini inamatatizo.",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Habari za muda,mimi PEREGIA FILIPO,hii namba yangu ya .Vp mbona shem PEREGIA FILIPO, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:",
        "Samahani naomba itume kwenye Airtel  .",
        "au iyo ela nitumie kwenye m-pesa hii  Jina litoke .",

        "Habari. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        "Naomba unitumie iyo Hela kwenye namba hii ya  . jina (Magomba Maila)",
        "Imethibitishwa, namba yako ya 0781476081 imejishindia TSH 2,000,000 kutoka TUZO POINT. Piga 0781476081 ili kupokea Hela yako.",
        "Au nitumie kwenye m-pesa Namba. jina litakuja ABDALLAH MWANAKU",

        "Iyo Pesa itume humu kwenye airtel 0676584303 jina lije MWANAIDI KHAMISI.",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",

        "tuma kwenye namba hii ya M-Pesa  jina litakuja HOSEA MKUMBUKWA Ukituma unijulishe",
        "Utanitumia kwenye ii 0755667788  jina JUMANNE YASINI MASAKA namba yangu inadeni usiitumie",
        "TUMIA NAMBA HII (0733822240)KUNITUMIA IYO HELA JINA LITAONYESHA (PEREGIA FILIPO)",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0755896103 AU 0755896103",
        "Utanitumia kwenye ii 0716484506  jina JENEROZA ROCK BENEDICTO namba yangu inadeni usiitumie",
        "VODA OFA hongera umepata zawadi Sh120000 milioni kutoka (VODA OFA) piga sim,.0733822240 kupata zawadi  asante",

        "mjukuu wangu utafuta ji wako mgumu hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0788542784",
        "0696530433 Jina litakuja MARIAM NDUGAI Nitumie kwenye hiyo ",
        "Imethibitishwa, namba yako ya  imejishindia TSH 1,500,000 kutoka Tuzo point. Piga  ili kupokea Hela yako.",
        "Habari za siku,mimi Magomba Maila,hii namba yangu ya voda.Vp mbona shem Magomba Maila, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",

        ", No need to go out work, just at home to earn 4,000,000TZS a day, please contact us: https://wa.me/2550695567435",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",

        "Tuzo point hongera umepata zawadi Sh2,000,000 milioni kutoka (Tuzo point) piga sim,.0676584303 kupata zawadi  asante",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        " F134 Imethibitishwa namba yako ya 061 ... imeshinda Tsh120000.00/=million kutoka Tuzo point ilikupokea Hela yako piga 0755667788 Asante",
        "ela tuma kwa namba hii  jina ",
        "Au nitumie kwenye M-Pesa Namba.0699137921 jina litakuja Magomba Maila",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By JUMANNE YASINI MASAKA,ni grp member",

        ", No need to go out work, just at home to earn 1,500,000TZS a day, please contact us: https://wa.me/255",

        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0781476081",
        "Imethibitishwa, namba yako ya  imejishindia TSH 170,000 kutoka Tuzo point. Piga  ili kupokea Hela yako.",
        "Tumia namba hii ya voda  kutuma hiyo Pesa jina ",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        ", No need to go out work, just at home to earn 170,000TZS a day, please contact us: https://wa.me/255",
        "Utanitumia kwenye ii 0755896103  jina  namba yangu inadeni usiitumie",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0654321098)(0654321098)",
        "IYO PESA ITUME KWENYE NAMBA HII 0716484506 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0750335946",
        "MPIGIE MZEE FEBU SHADI WILISON WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0747878264",
        "Naomba unitumie iyo Pesa kwenye namba hii ya  0786543210. jina (HOSEA MKUMBUKWA)",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0695567435 UKIWA TAYARI KUJIUNGA",
        "Iyo ela tuma humu kwenye  0617488472 Jina lije RAMATUNGU.",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "TUMIA NAMBA HII (0747878264)KUNITUMIA IYO HELA JINA LITAONYESHA (LINUSI MALALO)",
        "Congratulations! Your CV has passed. You can get 10,000,000TZS in a day. for details: wa.me/2550689592818",
        "TUZO  POINTI hongera umepata zawadi Sh5,000,000 milioni kutoka (TUZO  POINTI) piga sim,.0782435667 kupata zawadi  asante",

        ", No need to go out work, just at home to earn 6,000,000TZS a day, please contact us: https://wa.me/2550747878264",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA halotel NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "Utanitumia. kwemye namba 0782734560 ya halotel jina JUMANNE YASINI MASAKA.",
        "MZEE HOSEA MKUMBUKWA tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0755896103)(0755896103)",

        "Congratulations! Your CV has passed. You can get 2,000,000TZS in a day. for details: wa.me/2550699137921",
        "Congratulations! Your CV has passed. You can get 170,000TZS in a day. for details: wa.me/2550689592818",
        "Halotel ZBFL Imethibitishwa namba yako ya 074 ... imeshinda Tsh170,000.00/=million kutoka OFA YAKO ilikupokea ela yako piga  Asante",

        "Basi iyo hela nitumie kwenye namba hii 0787-406-889 jina litakuja () ile namba usitumie laini inamatatizo.",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        ", No need to go out work, just at home to earn 120000TZS a day, please contact us: https://wa.me/2550733822240",
        "Congratulations! Your CV has passed. You can get 170,000TZS in a day. for details: wa.me/2550750335946",
        "TUMIA NAMBA HII (0786543210)KUNITUMIA IYO HELA JINA LITAONYESHA ()",
        "Iyo ela tuma humu kwenye airtel 0755896103 Jina lije .",

        "Utanitumia kwenye ii 0755896103 Halotel jina NASHONI MBIRIBI namba yangu inadeni usiitumie",
        "Iyo ela tuma humu kwenye halotel 0695567435 Jina lije PEREGIA FILIPO.",

        "Tumia namba hii ya Halotel 0657666983 kutuma hiyo hela jina ",
        "Tumia namba hii ya halotel 0617488472 kutuma hiyo Pesa jina ",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0782435667",
        "Samahani naomba itume kwenye halotel 0773409724 .",

        "Iyo ela itume humu kwenye Halotel 0699137921 jina lije LINUSI MALALO.",
        "au iyo ela nitumie kwenye AirtelMoney hii  Jina litoke .",
        "MZEE RAMATUNGU tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0676584303)(0676584303)",

        "Utanitumia. kwemye namba 0654321098 ya airtel jina OLIVA MATIAS.",
        "Habari za siku. Mimi  mwenye nyumba wako hii namba yangu ya airtel. Mbona kimya na siku zinazidi kwenda...?",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0657666983 AU 0657666983",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0782435667 au 0782435667",

        "Basi iyo hela nitumie kwenye namba hii 0782435667 jina litakuja (NASHONI MBIRIBI) ile namba usitumie laini inamatatizo.",
        "au iyo ela nitumie kwenye pesa hii 0773409724 Jina litoke 0773409724.",
        "Iyo Pesa itume humu kwenye airtel 0782734560 jina lije MWANAIDI KHAMISI.",

        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0716484506",

        "mjukuu wangu utafuta ji wako mgumu ela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0755896103",
        "HALOTEL AQ78 Imethibitishwa namba yako ya 068 ... imeshinda Tsh10,000,000.00/=million kutoka TUZO  POINTI ilikupokea hela yako piga 0699137921 Asante",
        "Au nitumie kwenye pesa Namba.0733822240 jina litakuja MWANAIDI KHAMISI",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0782435667 UKIWA TAYARI KUJIUNGA",
        "Iyo ela tuma humu kwenye halotel 0689592818 Jina lije MARIAM NDUGAI.",
        "au iyo ela nitumie kwenye HaloPesa hii 0755896103 Jina litoke 0755896103.",
        "voda IUKB Imethibitishwa namba yako ya 078 ... imeshinda Tsh2,000,000.00/=million kutoka VODA OFA ilikupokea Pesa yako piga 0747878264 Asante",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA Halotel NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0689592818 AU 0689592818",
        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya airtel. Mbona kimya na siku zinazidi kwenda...?",

        "Iyo pesa itume humu kwenye  0716484506 jina lije .",

        "Congratulations! Your CV has passed. You can get 4,000,000TZS in a day. for details: wa.me/2550676584303",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0782435667 UKIWA TAYARI KUJIUNGA",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0782435667 UKIWA TAYARI KUJIUNGA",
        "Utanitumia kwa hîi HALOTEL 0689592818 j'ina ni Magomba Maila.",

        "TUMIA NAMBA HII (0773409724)KUNITUMIA IYO HELA JINA LITAONYESHA ()",

        "IYO PESA ITUME KWENYE NAMBA HII 0698018072 JINA ITALETA FEBU SHADI WILISON NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Imethibitishwa, namba yako ya 0755667788 imejishindia TSH 6,000,000 kutoka TUZO  POINTI. Piga 0755667788 ili kupokea Pesa yako.",
        ", No need to go out work, just at home to earn 4,000,000TZS a day, please contact us: https://wa.me/2550747878264",
        "MZEE JUMANNE YASINI MASAKA tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0698018072)(0698018072)",
        "TUZO  POINTI hongera umepata zawadi Sh2,000,000 milioni kutoka (TUZO  POINTI) piga sim,.0689592818 kupata zawadi  asante",
        ", No need to go out work, just at home to earn 6,000,000TZS a day, please contact us: https://wa.me/2550747878264",
        "Nitumie tu kwenye hii Halotel 0615810764 jina .",

        "Iyo ela tuma humu kwenye  0696530433 Jina lije NASHONI MBIRIBI",

        "Nitumie tu kwenye hii voda 0617488472 jina SAID MTAALAM .",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "Tumia namba hii ya  0676584303 kutuma hiyo ela jina JENEROZA ROCK BENEDICTO",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Congratulations! Your CV has passed. You can get 10,000,000TZS in a day. for details: wa.me/2550657538690",

        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0782734560 AU 0782734560",

        "Iyo ela tuma humu kwenye voda 0782734560 Jina lije HOSEA MKUMBUKWA.",

        "IYO PESA ITUME KWENYE NAMBA HII 0655251448 JINA ITALETA FEBU SHADI WILISON NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0716484506",
        "Iyo Pesa itume humu kwenye  0782734560 jina lije .",

        "ela tuma kwa namba hii  jina NASHONI MBIRIBI",

        "Nitumie tu kwenye hii Airtel 0733822240 jina SALOME KALUNGA.",
        "TUMIA NAMBA HII ()KUNITUMIA IYO HELA JINA LITAONYESHA (JUMANNE YASINI MASAKA)",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0696530433",

        "Utanitumia kwenye ii 0755896103 airtel jina SALOME KALUNGA namba yangu inadeni usiitumie",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "IYO PESA ITUME KWENYE NAMBA HII 0781476081 JINA ITALETA NASHONI MBIRIBI NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "mjukuu wangu utafuta ji wako mgumu ela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0655251448",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0617488472)(0617488472)",

        "Utanitumia kwa hîi AIRTEL 0782734560 j'ina ni .",

        "Mpigie Mzee HOSEA MKUMBUKWA kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0698018072",
        "MZEE PEREGIA FILIPO tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0699137921)(0699137921)",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "Congratulations! Your CV has passed. You can get 1,500,000TZS in a day. for details: wa.me/2550657538690",

        "Samahani naomba itume kwenye   Ester kalobelo.",
        "Nitumie tu kwenye hii AIRTEL 0696530433 jina .",

        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Nitumie tu kwenye hii   jina .",

        "Imethibitishwa, namba yako ya  imejishindia TSH 170,000 kutoka Tuzo point. Piga  ili kupokea ela yako.",

        "MPIGIE MZEE JUMANNE YASINI MASAKA WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0784862618",
        "Utanitumia. kwemye namba 0784862618 ya AIRTEL jina FEBU SHADI WILISON.",

        "Nitumie tu kwenye hii HALOTEL  jina MARIAM NDUGAI.",
        "Mpigie Mzee RAMATUNGU kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0781476081",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "au iyo ela nitumie kwenye M-Pesa hii 0782734560 Jina litoke 0782734560.",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0773409724",

        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0698018072",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0657666983 AU 0657666983",
        "Basi iyo hela nitumie kwenye namba hii 0698018072 jina litakuja (HOSEA MKUMBUKWA) ile namba usitumie laini inamatatizo.",
        "au iyo ela nitumie kwenye M-Pesa hii  Jina litoke .",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0655251448 AU 0655251448",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0787-406-889 UKIWA TAYARI KUJIUNGA",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA HALOTEL NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "TUZO POINT hongera umepata zawadi Sh2,000,000 milioni kutoka (TUZO POINT) piga sim,.0733822240 kupata zawadi  asante",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0698018072 au 0698018072",
        "Utanitumia kwa hîi Airtel 0716484506 j'ina ni .",
        "Au nitumie kwenye pesa Namba.0781476081 jina litakuja ",

        "Iyo ela tuma humu kwenye  0617488472 Jina lije SAID MTAALAM",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0784862618",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0788542784 au 0788542784",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",

        "Imethibitishwa, namba yako ya 0782734560 imejishindia TSH 6,000,000 kutoka Tuzo Point. Piga 0782734560 ili kupokea hela yako.",
        "MZEE ABDALLAH MWANAKU tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0657666983)(0657666983)",
        "Tumia namba hii ya  0750335946 kutuma hiyo pesa jina ",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "au iyo ela nitumie kwenye pesa hii 0655251448 Jina litoke 0655251448.",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0689592818",
        "Basi iyo hela nitumie kwenye namba hii 0755896103 jina litakuja (JUMANNE YASINI MASAKA) ile namba usitumie laini inamatatizo.",

        "TUMIA NAMBA HII (0676584303)KUNITUMIA IYO HELA JINA LITAONYESHA (MARIAM NDUGAI)",
        "mjukuu wangu utafuta ji wako mgumu ela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0676584303",
        "Habari za mda huu,mimi MWANAIDI KHAMISI,hii namba yangu ya AIRTEL.Vp mbona shem MWANAIDI KHAMISI, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu."

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ABDALLAH MWANAKU,ni grp member",
        "Iyo Pesa itume humu kwenye Halotel 0755667788 jina lije Magomba Maila.",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "We need urgently Need Staff salary 120000TZS. Reach HR team at: wa.me/255.",
        "Iyo hela itume humu kwenye Airtel  jina lije Magomba Maila.",

        "We need urgently Need Staff salary 1,500,000TZS. Reach HR team at: wa.me/255.",
        "Naomba unitumie iyo Pesa kwenye namba hii ya Airtel 0657666983. jina (Magomba Maila)",

        "Tuzo point hongera umepata zawadi Sh1,500,000 milioni kutoka (Tuzo point) piga sim,.0784862618 kupata zawadi  asante",
        "Basi iyo hela nitumie kwenye namba hii  jina litakuja (LINUSI MALALO) ile namba usitumie laini inamatatizo.",

        "VODA OFA hongera umepata zawadi Sh170,000 milioni kutoka (VODA OFA) piga sim,.0615810764 kupata zawadi  asante",
        "Mpigie Mzee Ester kalobelo kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga ",
        "Au nitumie kwenye m-pesa Namba.0786543210 jina litakuja NASHONI MBIRIBI",
        "Au nitumie kwenye AirtelMoney Namba.0787-406-889 jina litakuja ",

        "Habari za asubuhi,mimi JENEROZA ROCK BENEDICTO,hii namba yangu ya .Vp mbona shem JENEROZA ROCK BENEDICTO, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "TUMIA NAMBA HII (0773409724)KUNITUMIA IYO HELA JINA LITAONYESHA ()",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0781476081 UKIWA TAYARI KUJIUNGA",
        "tuma kwenye namba hii ya M-Pesa  jina litakuja ABDALLAH MWANAKU Ukituma unijulishe",

        "Tuzo point hongera umepata zawadi Sh1,500,000 milioni kutoka (Tuzo point) piga sim,.0787-406-889 kupata zawadi  asante",
        "Congratulations! Your CV has passed. You can get 1,500,000TZS in a day. for details: wa.me/2550699137",
        "Au nitumie kwenye AirtelMoney Namba.0784862618 jina litakuja ",
        "Iyo ela tuma humu kwenye Airtel 0788542784 Jina lije .",

        "Utanitumia kwenye ii  halotel jina NASHONI MBIRIBI namba yangu inadeni usiitumie",
        "Tumia namba hii ya HALOTEL 0782435667 kutuma hiyo hela jina LINUSI MALALO",
        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0657666983",

        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0699137921 au 0699137921",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0676584303 AU 0676584303",
        "IYO PESA ITUME KWENYE NAMBA HII 0755667788 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        ", No need to go out work, just at home to earn 170,000TZS a day, please contact us: https://wa.me/2550747878264",
        "0786543210 Jina litakuja NASHONI MBIRIBI Nitumie kwenye hiyo ",

        "au iyo ela nitumie kwenye m-pesa hii 0698018072 Jina litoke 0698018072.",
        "Congratulations! Your CV has passed. You can get 10,000,000TZS in a day. for details: wa.me/2550617488472",
        ", No need to go out work, just at home to earn 10,000,000TZS a day, please contact us: https://wa.me/2550773409724",
        "Utanitumia kwenye ii  Halotel jina Ester kalobelo namba yangu inadeni usiitumie",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Imethibitishwa, namba yako ya 0654321098 imejishindia TSH 5,000,000 kutoka VODA OFA. Piga 0654321098 ili kupokea Pesa yako.",

        "au iyo ela nitumie kwenye pesa hii 0788542784 Jina litoke 0788542784.",

        "Congratulations! Your CV has passed. You can get 10,000,000TZS in a day. for details: wa.me/2550782734560",
        "IYO PESA ITUME KWENYE NAMBA HII 0676584303 JINA ITALETA FEBU SHADI WILISON NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "VODA OFA hongera umepata zawadi Sh2,000,000 milioni kutoka (VODA OFA) piga sim,.0657538690 kupata zawadi  asante",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA Magomba Maila NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",

        "Iyo ela itume humu kwenye  0784862618 jina lije PEREGIA FILIPO.",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0733822240 UKIWA TAYARI KUJIUNGA",
        "Naomba unitumie iyo hela kwenye namba hii ya AIRTEL 0699137921. jina (HOSEA MKUMBUKWA)",
        "Naomba unitumie iyo Pesa kwenye namba hii ya airtel 0773409724. jina (PEREGIA FILIPO)",
        ", No need to go out work, just at home to earn 170,000TZS a day, please contact us: https://wa.me/255",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By MWANAIDI KHAMISI,ni grp member",
        "Pesa tuma kwa namba hii 0716484506 jina ",

        "Samahani naomba itume kwenye HALOTEL  SAID MTAALAM .",
        "Habari za mda huu. Mimi  mwenye nyumba wako hii namba yangu ya Airtel. Mbona kimya na siku zinazidi kwenda...?",
        "Iyo ela tuma humu kwenye airtel 0615810764 Jina lije ",

        "Utanitumia. kwemye namba  ya  jina .",
        "Utanitumia kwa hîi  0698018072 j'ina ni .",
        "IYO PESA ITUME KWENYE NAMBA HII 0617488472 JINA ITALETA Ester kalobelo NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "Hela tuma kwa namba hii 0655251448 jina SAID MTAALAM ",
        "MPIGIE MZEE HOSEA MKUMBUKWA WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0695567435",
        "au iyo ela nitumie kwenye m-pesa hii 0699137921 Jina litoke 0699137921.",

        "Nitumie tu kwenye hii HALOTEL 0733822240 jina Ester kalobelo.",
        "Tumia namba hii ya   kutuma hiyo ela jina ",
        "Utanitumia kwa hîi  0689592818 j'ina ni .",
        "Utanitumia kwenye ii 0782435667  jina MWANAIDI KHAMISI namba yangu inadeni usiitumie",
        ", No need to go out work, just at home to earn 2,000,000TZS a day, please contact us: https://wa.me/2550655251448",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",
        "Naomba unitumie iyo pesa kwenye namba hii ya AIRTEL . jina (PEREGIA FILIPO)",
        "Tumia namba hii ya AIRTEL 0655251448 kutuma hiyo Hela jina PEREGIA FILIPO",

        "Utanitumia kwa hîi  0698018072 j'ina ni MWANAIDI KHAMISI.",
        "MZEE PEREGIA FILIPO tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga ()()",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0733822240 AU 0733822240",

        "Basi iyo hela nitumie kwenye namba hii 0698018072 jina litakuja (JUMANNE YASINI MASAKA) ile namba usitumie laini inamatatizo.",

        "TUMIA NAMBA HII (0716484506)KUNITUMIA IYO HELA JINA LITAONYESHA (JENEROZA ROCK BENEDICTO)",

        "We need urgently Need Staff salary 4,000,000TZS. Reach HR team at: wa.me/2550782435667.",
        "Naomba unitumie iyo ela kwenye namba hii ya  0787-406-889. jina (MARIAM NDUGAI)",
        "Utanitumia kwenye ii 0699137921  jina SALOME KALUNGA namba yangu inadeni usiitumie",

        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0733822240",

        "tuma kwenye namba hii ya pesa 0698018072 jina litakuja  Ukituma unijulishe",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0787-406-889 UKIWA TAYARI KUJIUNGA",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0615810764 UKIWA TAYARI KUJIUNGA",
        " YR89 Imethibitishwa namba yako ya 078 ... imeshinda Tsh2,000,000.00/=million kutoka Tuzo point ilikupokea ela yako piga 0654321098 Asante",

        "Au nitumie kwenye M-Pesa Namba.0782435667 jina litakuja Ester kalobelo",
        "Samahani naomba itume kwenye   .",
        "hela tuma kwa namba hii 0657666983 jina MARIAM NDUGAI",
        "au iyo ela nitumie kwenye m-pesa hii 0755667788 Jina litoke 0755667788.",
        "tuma kwenye namba hii ya HaloPesa 0657538690 jina litakuja Ester kalobelo Ukituma unijulishe",
        "Iyo ela itume humu kwenye HALOTEL 0657538690 jina lije SAID MTAALAM .",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",
        ", No need to go out work, just at home to earn 10,000,000TZS a day, please contact us: https://wa.me/2550654321098",
        "Tumia namba hii ya   kutuma hiyo ela jina SALOME KALUNGA",
        "Tuzo Point hongera umepata zawadi Sh170,000 milioni kutoka (Tuzo Point) piga sim,.0782734560 kupata zawadi  asante",

        "Habari za muda,mimi PEREGIA FILIPO,hii namba yangu ya .Vp mbona shem PEREGIA FILIPO, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "TUMIA NAMBA HII (0781476081)KUNITUMIA IYO HELA JINA LITAONYESHA ()",
        "Iyo ela tuma humu kwenye  0782734560 Jina lije MWANAIDI KHAMISI.",

        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0617488472",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0733822240 AU 0733822240",
        "Mpigie Mzee RAMATUNGU kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0750335946",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0689592818 AU 0689592818",
        "Mpigie Mzee PEREGIA FILIPO kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga ",
        "Iyo ela tuma humu kwenye Halotel  Jina lije .",

        "Utanitumia kwenye ii  voda jina FEBU SHADI WILISON namba yangu inadeni usiitumie",

        ", No need to go out work, just at home to earn 6,000,000TZS a day, please contact us: https://wa.me/2550655251448",
        "IYO PESA ITUME KWENYE NAMBA HII 0657538690 JINA ITALETA Magomba Maila NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "Utanitumia. kwemye namba 0657666983 ya  jina RAMATUNGU.",
        ", No need to go out work, just at home to earn 1,500,000TZS a day, please contact us: https://wa.me/2550655251448",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0733822240)(0733822240)",
        "ela tuma kwa namba hii 0787-406-889 jina ",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By PEREGIA FILIPO,ni grp member",
        "Iyo Hela itume humu kwenye voda  jina lije .",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0787-406-889",

        "mjukuu wangu utafuta ji wako mgumu hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0695567435",
        "Utanitumia. kwemye namba 0733822240 ya AIRTEL jina .",
        "TUMIA NAMBA HII (0786543210)KUNITUMIA IYO HELA JINA LITAONYESHA ()",

        "We need urgently Need Staff salary 170,000TZS. Reach HR team at: wa.me/2550755896103.",
        "OFA YAKO hongera umepata zawadi Sh170,000 milioni kutoka (OFA YAKO) piga sim,.0654321098 kupata zawadi  asante",
        "TUMIA NAMBA HII (0782435667)KUNITUMIA IYO HELA JINA LITAONYESHA (Magomba Maila)",
        "pesa tuma kwa namba hii 0750335946 jina ",

        "We need urgently Need Staff salary 120000TZS. Reach HR team at: wa.me/255.",
        "We need urgently Need Staff salary 120000TZS. Reach HR team at: wa.me/2550699137921.",
        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0786543210",

        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0696530433",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0655251448 AU 0655251448",
        "au iyo ela nitumie kwenye m-pesa hii 0755667788 Jina litoke 0755667788.",
        "Basi iyo hela nitumie kwenye namba hii 0617488472 jina litakuja () ile namba usitumie laini inamatatizo.",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0698018072)(0698018072)",

        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0782734560 AU 0782734560",

        "Nitumie tu kwenye hii  0716484506 jina ABDALLAH MWANAKU.",
        "Basi iyo hela nitumie kwenye namba hii 0655251448 jina litakuja (Magomba Maila) ile namba usitumie laini inamatatizo.",

        "VODA OFA hongera umepata zawadi Sh120000 milioni kutoka (VODA OFA) piga sim,. kupata zawadi  asante",

        "We need urgently Need Staff salary 10,000,000TZS. Reach HR team at: wa.me/255.",
        ", No need to go out work, just at home to earn 6,000,000TZS a day, please contact us: https://wa.me/2550755667788",
        "MPIGIE MZEE RAMATUNGU WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA ",
        "OFA YAKO hongera umepata zawadi Sh120000 milioni kutoka (OFA YAKO) piga sim,.0773409724 kupata zawadi  asante",
        "Utanitumia kwa hîi Halotel 0782734560 j'ina ni Magomba Maila.",
        "Nitumie tu kwenye hii HALOTEL  jina Magomba Maila.",

        "Iyo Pesa itume humu kwenye halotel  jina lije PEREGIA FILIPO.",
        "Naomba unitumie iyo hela kwenye namba hii ya  0747878264. jina (PEREGIA FILIPO)",

        "mjukuu wangu utafuta ji wako mgumu hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0782734560",

        "0750335946 Jina litakuja LINUSI MALALO Nitumie kwenye hiyo AIRTEL",
        "Imethibitishwa, namba yako ya 0689592818 imejishindia TSH 6,000,000 kutoka TUZO POINT. Piga 0689592818 ili kupokea pesa yako.",
        "Iyo hela itume humu kwenye HALOTEL 0781476081 jina lije .",

        "tuma kwenye namba hii ya HaloPesa 0696530433 jina litakuja SAID MTAALAM  Ukituma unijulishe",

        "Congratulations! Your CV has passed. You can get 6,000,000TZS in a day. for details: wa.me/2550755667788",
        "Au nitumie kwenye HaloPesa Namba.0657538690 jina litakuja Magomba Maila",
        "Habari za mda huu. Mimi  mwenye nyumba wako hii namba yangu ya airtel. Mbona kimya na siku zinazidi kwenda...?",
        "IYO PESA ITUME KWENYE NAMBA HII 0773409724 JINA ITALETA OLIVA MATIAS NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "TUMIA NAMBA HII ()KUNITUMIA IYO HELA JINA LITAONYESHA ()",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "Habari za asubuhi,mimi JUMANNE YASINI MASAKA,hii namba yangu ya .Vp mbona shem JUMANNE YASINI MASAKA, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA halotel NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "OFA YAKO hongera umepata zawadi Sh2,000,000 milioni kutoka (OFA YAKO) piga sim,.0786543210 kupata zawadi  asante",

        "Habari za siku. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0696530433",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By OLIVA MATIAS,ni grp member",
        "Tuzo point hongera umepata zawadi Sh10,000,000 milioni kutoka (Tuzo point) piga sim,.0695567435 kupata zawadi  asante",
        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0755667788",

        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0773409724 AU 0773409724",
        "Utanitumia. kwemye namba 0755667788 ya  jina NASHONI MBIRIBI.",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "au iyo ela nitumie kwenye HaloPesa hii  Jina litoke .",
        "au iyo ela nitumie kwenye AirtelMoney hii 0699137921 Jina litoke 0699137921.",
        ", No need to go out work, just at home to earn 4,000,000TZS a day, please contact us: https://wa.me/255",
        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya HALOTEL. Mbona kimya na siku zinazidi kwenda...?",

        "Utanitumia. kwemye namba 0696530433 ya AIRTEL jina Ester kalobelo.",
        "MZEE Ester kalobelo tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga ()()",
        "TUMIA NAMBA HII (0755667788)KUNITUMIA IYO HELA JINA LITAONYESHA (JENEROZA ROCK BENEDICTO)",
        "Habari za mda huu. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        ", No need to go out work, just at home to earn 5,000,000TZS a day, please contact us: https://wa.me/2550781476081",

        "Utanitumia kwa hîi  0698018072 j'ina ni LINUSI MALALO.",
        "TUMIA NAMBA HII (0781476081)KUNITUMIA IYO HELA JINA LITAONYESHA (Magomba Maila)",
        "Utanitumia. kwemye namba  ya AIRTEL jina LINUSI MALALO.",
        "Congratulations! Your CV has passed. You can get 2,000,000TZS in a day. for details: wa.me/2550788542784",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0654321098",
        "Tuzo Point hongera umepata zawadi Sh5,000,000 milioni kutoka (Tuzo Point) piga sim,.0747878264 kupata zawadi  asante",

        "Habari za mchana,mimi JUMANNE YASINI MASAKA,hii namba yangu ya Airtel.Vp mbona shem JUMANNE YASINI MASAKA, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",
        "MPIGIE MZEE Magomba Maila WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA ",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0655251448 au 0655251448",

        "TUMIA NAMBA HII (0787-406-889)KUNITUMIA IYO HELA JINA LITAONYESHA (FEBU SHADI WILISON)",
        "Naomba unitumie iyo pesa kwenye namba hii ya  0784862618. jina (MWANAIDI KHAMISI)",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0755667788)(0755667788)",
        ", No need to go out work, just at home to earn 1,500,000TZS a day, please contact us: https://wa.me/2550773409724",
        "0617488472 Jina litakuja Magomba Maila Nitumie kwenye hiyo ",
        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0773409724",
        "Habari za muda. Mimi  mwenye nyumba wako hii namba yangu ya HALOTEL. Mbona kimya na siku zinazidi kwenda...?",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0733822240 UKIWA TAYARI KUJIUNGA",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0615810764 au 0615810764",
        "tuma kwenye namba hii ya AirtelMoney 0696530433 jina litakuja SAID MTAALAM  Ukituma unijulishe",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By LINUSI MALALO,ni grp member",

        "Iyo hela itume humu kwenye  0695567435 jina lije Ester kalobelo.",

        ", No need to go out work, just at home to earn 10,000,000TZS a day, please contact us: https://wa.me/2550655251448",
        " Jina litakuja  Nitumie kwenye hiyo AIRTEL",
        "We need urgently Need Staff salary 10,000,000TZS. Reach HR team at: wa.me/2550784862618.",

        "Nitumie tu kwenye hii voda 0773409724 jina .",
        "Airtel ENLC Imethibitishwa namba yako ya 078 ... imeshinda Tsh170,000.00/=million kutoka OFA YAKO ilikupokea ela yako piga 0657666983 Asante",
        "TUMIA NAMBA HII (0787-406-889)KUNITUMIA IYO HELA JINA LITAONYESHA ()",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0784862618 UKIWA TAYARI KUJIUNGA",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0781476081 UKIWA TAYARI KUJIUNGA",
        "Samahani naomba itume kwenye   Ester kalobelo.",
        " Jina litakuja RAMATUNGU Nitumie kwenye hiyo ",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "tuma kwenye namba hii ya m-pesa 0784862618 jina litakuja  Ukituma unijulishe",
        "Utanitumia kwenye ii 0676584303  jina FEBU SHADI WILISON namba yangu inadeni usiitumie",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0733822240 UKIWA TAYARI KUJIUNGA",

        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Habari za muda. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        " W1SD Imethibitishwa namba yako ya 078 ... imeshinda Tsh1,500,000.00/=million kutoka OFA YAKO ilikupokea Pesa yako piga 0716484506 Asante",

        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya airtel. Mbona kimya na siku zinazidi kwenda...?",
        "Utanitumia kwenye ii 0689592818 airtel jina RAMATUNGU namba yangu inadeni usiitumie",
        "Habari za asubuhi,mimi ,hii namba yangu ya .Vp mbona shem , anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",

        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0784862618)(0784862618)",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0699137921",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "Basi iyo hela nitumie kwenye namba hii 0782435667 jina litakuja () ile namba usitumie laini inamatatizo.",
        "Utanitumia kwenye ii 0689592818 Airtel jina JUMANNE YASINI MASAKA namba yangu inadeni usiitumie",
        ", No need to go out work, just at home to earn 4,000,000TZS a day, please contact us: https://wa.me/2550786543210",

        "mjukuu wangu utafuta ji wako mgumu hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0755896103",

        "tuma kwenye namba hii ya AirtelMoney  jina litakuja  Ukituma unijulishe",

        "au iyo ela nitumie kwenye M-Pesa hii 0698018072 Jina litoke 0698018072.",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0773409724",

        "Basi iyo hela nitumie kwenye namba hii 0657538690 jina litakuja () ile namba usitumie laini inamatatizo.",
        "We need urgently Need Staff salary 170,000TZS. Reach HR team at: wa.me/2550755667788.",
        "Iyo ela tuma humu kwenye airtel 0615810764 Jina lije OLIVA MATIAS.",

        "Habari za mda huu. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "Au nitumie kwenye AirtelMoney Namba.0657666983 jina litakuja NASHONI MBIRIBI",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA Ester kalobelo NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",

        "Congratulations! Your CV has passed. You can get 5,000,000TZS in a day. for details: wa.me/2550696530433",
        "Iyo ela itume humu kwenye  0654321098 jina lije .",
        "Congratulations! Your CV has passed. You can get 170,000TZS in a day. for details: wa.me/255",

        "Habari za asubuhi,mimi SAID MTAALAM ,hii namba yangu ya .Vp mbona shem SAID MTAALAM , anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",

        "Congratulations! Your CV has passed. You can get 1,500,000TZS in a day. for details: wa.me/2550784862618",

        "Congratulations! Your CV has passed. You can get 10,000,000TZS in a day. for details: wa.me/2550784862618",

        "voda QI2J Imethibitishwa namba yako ya 067 ... imeshinda Tsh2,000,000.00/=million kutoka OFA YAKO ilikupokea Hela yako piga 0617488472 Asante",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",
        "Naomba unitumie iyo Hela kwenye namba hii ya  0747878264. jina ()",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0782734560 AU 0782734560",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",

        "Iyo ela itume humu kwenye AIRTEL 0696530433 jina lije Magomba Maila.",
        "pesa tuma kwa namba hii 0773409724 jina JUMANNE YASINI MASAKA",
        "We need urgently Need Staff salary 170,000TZS. Reach HR team at: wa.me/2550676584303.",
        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0676584303",
        "Imethibitishwa, namba yako ya 0782734560 imejishindia TSH 10,000,000 kutoka OFA YAKO. Piga 0782734560 ili kupokea Pesa yako.",
        "We need urgently Need Staff salary 170,000TZS. Reach HR team at: wa.me/2550695567435.",

        "Basi iyo hela nitumie kwenye namba hii  jina litakuja () ile namba usitumie laini inamatatizo.",

        "We need urgently Need Staff salary 4,000,000TZS. Reach HR team at: wa.me/2550695567435.",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0786543210",
        "Basi iyo hela nitumie kwenye namba hii 0781476081 jina litakuja (MARIAM NDUGAI) ile namba usitumie laini inamatatizo.",

        "Iyo Pesa itume humu kwenye halotel 0788542784 jina lije .",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0676584303)(0676584303)",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Iyo ela tuma humu kwenye AIRTEL 0654321098 Jina lije ABDALLAH MWANAKU",
        "Utanitumia kwenye ii 0699137921  jina SALOME KALUNGA namba yangu inadeni usiitumie",
        "Habari za siku,mimi MARIAM NDUGAI,hii namba yangu ya airtel.Vp mbona shem MARIAM NDUGAI, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0773409724)(0773409724)",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ,ni grp member",
        "Iyo hela itume humu kwenye  0655251448 jina lije MARIAM NDUGAI.",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0657538690",

        "IYO PESA ITUME KWENYE NAMBA HII 0773409724 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Tumia namba hii ya airtel 0615810764 kutuma hiyo Hela jina Magomba Maila",
        "TUMIA NAMBA HII (0716484506)KUNITUMIA IYO HELA JINA LITAONYESHA ()",
        "Iyo pesa itume humu kwenye halotel 0786543210 jina lije ABDALLAH MWANAKU.",
        "Habari za mda huu. Mimi  mwenye nyumba wako hii namba yangu ya Halotel. Mbona kimya na siku zinazidi kwenda...?",

        "Tumia namba hii ya AIRTEL 0750335946 kutuma hiyo pesa jina Magomba Maila",

        "IYO PESA ITUME KWENYE NAMBA HII 0747878264 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0782435667 AU 0782435667",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0781476081 au 0781476081",

        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0695567435",
        "Utanitumia kwenye ii 0657666983 airtel jina PEREGIA FILIPO namba yangu inadeni usiitumie",
        "Au nitumie kwenye AirtelMoney Namba.0698018072 jina litakuja JUMANNE YASINI MASAKA",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0689592818 AU 0689592818",
        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0676584303",

        "au iyo ela nitumie kwenye pesa hii 0617488472 Jina litoke 0617488472.",
        "MZEE OLIVA MATIAS tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0787-406-889)(0787-406-889)",

        "tuma kwenye namba hii ya HaloPesa 0657666983 jina litakuja  Ukituma unijulishe",

        "Imethibitishwa, namba yako ya 0747878264 imejishindia TSH 4,000,000 kutoka OFA YAKO. Piga 0747878264 ili kupokea Pesa yako.",
        "Congratulations! Your CV has passed. You can get 6,000,000TZS in a day. for details: wa.me/2550615810764",
        "hela tuma kwa namba hii 0698018072 jina SALOME KALUNGA",
        "Pesa tuma kwa namba hii 0657538690 jina ",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:",
        "Naomba unitumie iyo pesa kwenye namba hii ya  . jina ()",

        "Utanitumia kwenye ii 0781476081  jina HOSEA MKUMBUKWA namba yangu inadeni usiitumie",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:0784862618",
        "Congratulations! Your CV has passed. You can get 120000TZS in a day. for details: wa.me/2550655251448",
        ", No need to go out work, just at home to earn 2,000,000TZS a day, please contact us: https://wa.me/2550689592818",
        "MZEE HOSEA MKUMBUKWA tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0615810764)(0615810764)",
        "Imethibitishwa, namba yako ya  imejishindia TSH 6,000,000 kutoka TUZO  POINTI. Piga  ili kupokea hela yako.",
        "We need urgently Need Staff salary 170,000TZS. Reach HR team at: wa.me/2550782734560.",
        "Utanitumia kwa hîi halotel  j'ina ni PEREGIA FILIPO.",
        "Iyo Hela itume humu kwenye  0786543210 jina lije ABDALLAH MWANAKU.",

        "hela tuma kwa namba hii 0617488472 jina ABDALLAH MWANAKU",

        "Utanitumia kwenye ii 0698018072 halotel jina SAID MTAALAM  namba yangu inadeni usiitumie",
        "IYO PESA ITUME KWENYE NAMBA HII 0755667788 JINA ITALETA JENEROZA ROCK BENEDICTO NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Utanitumia kwenye ii 0787-406-889  jina PEREGIA FILIPO namba yangu inadeni usiitumie",
        "Imethibitishwa, namba yako ya 0782734560 imejishindia TSH 4,000,000 kutoka TUZO POINT. Piga 0782734560 ili kupokea pesa yako.",
        "Iyo ela tuma humu kwenye voda 0689592818 Jina lije .",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA HALOTEL NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",

        "Iyo ela tuma humu kwenye  0784862618 Jina lije PEREGIA FILIPO",
        "Congratulations! Your CV has passed. You can get 4,000,000TZS in a day. for details: wa.me/2550782435667",
        "TUMIA NAMBA HII (0617488472)KUNITUMIA IYO HELA JINA LITAONYESHA ()",
        "tuma kwenye namba hii ya M-Pesa 0782734560 jina litakuja MARIAM NDUGAI Ukituma unijulishe",

        "Utanitumia kwenye ii   jina SAID MTAALAM  namba yangu inadeni usiitumie",

        "We need urgently Need Staff salary 2,000,000TZS. Reach HR team at: wa.me/2550695567435.",
        "Nitumie tu kwenye hii Airtel  jina .",

        "voda ZYBU Imethibitishwa namba yako ya 065 ... imeshinda Tsh2,000,000.00/=million kutoka OFA YAKO ilikupokea hela yako piga 0698018072 Asante",
        "0782734560 Jina litakuja NASHONI MBIRIBI Nitumie kwenye hiyo airtel",
        "MPIGIE MZEE LINUSI MALALO WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0696530433",
        "Iyo Pesa itume humu kwenye AIRTEL 0788542784 jina lije .",
        "TUMIA NAMBA HII ()KUNITUMIA IYO HELA JINA LITAONYESHA (FEBU SHADI WILISON)",
        "Mpigie Mzee MWANAIDI KHAMISI kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0689592818",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Nitumie tu kwenye hii  0733822240 jina SALOME KALUNGA.",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",

        "Utanitumia. kwemye namba 0784862618 ya  jina Magomba Maila.",
        "Iyo ela tuma humu kwenye  0773409724 Jina lije NASHONI MBIRIBI.",

        "Mpigie Mzee SALOME KALUNGA kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0788542784",
        "Basi iyo hela nitumie kwenye namba hii 0699137921 jina litakuja (SALOME KALUNGA) ile namba usitumie laini inamatatizo.",
        "Iyo ela itume humu kwenye  0615810764 jina lije .",

        "VODA OFA hongera umepata zawadi Sh5,000,000 milioni kutoka (VODA OFA) piga sim,.0750335946 kupata zawadi  asante",

        "tuma kwenye namba hii ya pesa  jina litakuja MWANAIDI KHAMISI Ukituma unijulishe",
        "Utanitumia kwenye ii 0695567435  jina PEREGIA FILIPO namba yangu inadeni usiitumie",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0696530433 UKIWA TAYARI KUJIUNGA",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0699137921 au 0699137921",

        " IG2A Imethibitishwa namba yako ya 078 ... imeshinda Tsh6,000,000.00/=million kutoka Tuzo point ilikupokea ela yako piga 0782435667 Asante",

        "We need urgently Need Staff salary 1,500,000TZS. Reach HR team at: wa.me/2550750335946.",

        "Nitumie tu kwenye hii halotel 0657666983 jina SAID MTAALAM .",
        "IYO PESA ITUME KWENYE NAMBA HII 0676584303 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "0755667788 Jina litakuja PEREGIA FILIPO Nitumie kwenye hiyo ",

        "Utanitumia kwa hîi  0782734560 j'ina ni .",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0787-406-889 AU 0787-406-889",

        "Mpigie Mzee  kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0689592818",
        "Nitumie tu kwenye hii HALOTEL 0657666983 jina JUMANNE YASINI MASAKA.",

        "au iyo ela nitumie kwenye HaloPesa hii 0755667788 Jina litoke 0755667788.",
        "tuma kwenye namba hii ya M-Pesa 0773409724 jina litakuja SALOME KALUNGA Ukituma unijulishe",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",
        "Tumia namba hii ya  0781476081 kutuma hiyo pesa jina ",

        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0696530433",
        "Imethibitishwa, namba yako ya 0788542784 imejishindia TSH 1,500,000 kutoka OFA YAKO. Piga 0788542784 ili kupokea Pesa yako.",
        " Jina litakuja  Nitumie kwenye hiyo voda",
        "Habari,mimi ,hii namba yangu ya .Vp mbona shem , anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "HALOTEL 7D0B Imethibitishwa namba yako ya 075 ... imeshinda Tsh6,000,000.00/=million kutoka TUZO  POINTI ilikupokea Hela yako piga  Asante",
        "MZEE HOSEA MKUMBUKWA tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0781476081)(0781476081)",
        "Basi iyo hela nitumie kwenye namba hii 0695567435 jina litakuja (MARIAM NDUGAI) ile namba usitumie laini inamatatizo.",

        "We need urgently Need Staff salary 6,000,000TZS. Reach HR team at: wa.me/2550657538690.",
        "Iyo ela tuma humu kwenye  0787-406-889 Jina lije .",

        "Utanitumia. kwemye namba 0782734560 ya  jina .",
        "Tumia namba hii ya Halotel 0654321098 kutuma hiyo hela jina ",

        "MPIGIE MZEE JUMANNE YASINI MASAKA WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA ",

        "Naomba unitumie iyo hela kwenye namba hii ya Airtel 0782435667. jina ()",
        "Nitumie tu kwenye hii Airtel 0755896103 jina SAID MTAALAM .",

        "Iyo ela tuma humu kwenye halotel  Jina lije MARIAM NDUGAI",

        "MZEE Ester kalobelo tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0676584303)(0676584303)",
        "Hela tuma kwa namba hii 0750335946 jina Magomba Maila",
        "Nitumie tu kwenye hii  0654321098 jina Ester kalobelo.",
        "Iyo Hela itume humu kwenye Halotel 0657666983 jina lije .",
        "Samahani naomba itume kwenye Halotel 0689592818 .",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",

        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0784862618",
        "Imethibitishwa, namba yako ya  imejishindia TSH 10,000,000 kutoka VODA OFA. Piga  ili kupokea hela yako.",

        ", No need to go out work, just at home to earn 10,000,000TZS a day, please contact us: https://wa.me/2550755667788",

        "tuma kwenye namba hii ya HaloPesa 0750335946 jina litakuja LINUSI MALALO Ukituma unijulishe",
        "Iyo ela tuma humu kwenye HALOTEL 0781476081 Jina lije Ester kalobelo",
        "MZEE JENEROZA ROCK BENEDICTO tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga ()()",

        "Iyo ela tuma humu kwenye voda 0773409724 Jina lije ABDALLAH MWANAKU",

        "Basi iyo hela nitumie kwenye namba hii  jina litakuja (NASHONI MBIRIBI) ile namba usitumie laini inamatatizo.",
        "Airtel 94DY Imethibitishwa namba yako ya 078 ... imeshinda Tsh2,000,000.00/=million kutoka OFA YAKO ilikupokea ela yako piga 0698018072 Asante",
        "Utanitumia. kwemye namba 0699137921 ya HALOTEL jina .",
        " 5HKP Imethibitishwa namba yako ya 078 ... imeshinda Tsh10,000,000.00/=million kutoka OFA YAKO ilikupokea ela yako piga  Asante",
        "Utanitumia kwa hîi  0750335946 j'ina ni LINUSI MALALO.",

        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",
        "Iyo ela tuma humu kwenye HALOTEL 0755667788 Jina lije OLIVA MATIAS.",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By NASHONI MBIRIBI,ni grp member",
        "Utanitumia kwa hîi HALOTEL 0615810764 j'ina ni .",
        "TUMIA NAMBA HII (0689592818)KUNITUMIA IYO HELA JINA LITAONYESHA (Magomba Maila)",

        "Au nitumie kwenye AirtelMoney Namba.0696530433 jina litakuja Magomba Maila",
        "Habari za muda. Mimi  mwenye nyumba wako hii namba yangu ya Airtel. Mbona kimya na siku zinazidi kwenda...?",
        "mjukuu wangu utafuta ji wako mgumu ela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0695567435",

        "Utanitumia kwenye ii 0733822240 voda jina  namba yangu inadeni usiitumie",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0676584303 AU 0676584303",
        "Iyo Pesa itume humu kwenye  0617488472 jina lije SALOME KALUNGA.",

        "Iyo Pesa itume humu kwenye halotel 0615810764 jina lije LINUSI MALALO.",

        "Habari za siku,mimi ,hii namba yangu ya .Vp mbona shem , anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0698018072 UKIWA TAYARI KUJIUNGA",
        "Tumia namba hii ya  0781476081 kutuma hiyo ela jina ",
        "ela tuma kwa namba hii 0750335946 jina ",
        "We need urgently Need Staff salary 5,000,000TZS. Reach HR team at: wa.me/2550781476081.",
        "Au nitumie kwenye M-Pesa Namba.0696530433 jina litakuja OLIVA MATIAS",
        "Habari za siku,mimi MARIAM NDUGAI,hii namba yangu ya .Vp mbona shem MARIAM NDUGAI, anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        "Utanitumia kwenye ii 0699137921  jina  namba yangu inadeni usiitumie",

        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",

        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0655251448 au 0655251448",

        "(6,6,6)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI, BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJI,ONGEA NA WAKALA WETU:",
        "Utanitumia kwa hîi  0781476081 j'ina ni .",

        "Habari za mda huu,mimi SAID MTAALAM ,hii namba yangu ya .Vp mbona shem SAID MTAALAM , anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",

        "Pesa tuma kwa namba hii  jina ",
        "Iyo ela tuma humu kwenye  0750335946 Jina lije Magomba Maila.",

        "Utanitumia kwenye ii 0784862618  jina  namba yangu inadeni usiitumie",
        "We need urgently Need Staff salary 2,000,000TZS. Reach HR team at: wa.me/2550698018072.",

        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Imethibitishwa, namba yako ya 0617488472 imejishindia TSH 170,000 kutoka Tuzo Point. Piga 0617488472 ili kupokea pesa yako.",
        " Jina litakuja JENEROZA ROCK BENEDICTO Nitumie kwenye hiyo Halotel",
        "au iyo ela nitumie kwenye M-Pesa hii 0698018072 Jina litoke 0698018072.",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0698018072",
        "Au nitumie kwenye M-Pesa Namba. jina litakuja JENEROZA ROCK BENEDICTO",
        "We need urgently Need Staff salary 6,000,000TZS. Reach HR team at: wa.me/2550787-406-889.",
        "MZEE SAID MTAALAM  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga ()()",
        "Naomba unitumie iyo hela kwenye namba hii ya  0747878264. jina (FEBU SHADI WILISON)",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0781476081 AU 0781476081",

        "Naomba unitumie iyo Pesa kwenye namba hii ya  0782435667. jina (RAMATUNGU)",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Utanitumia kwenye ii 0755896103  jina  namba yangu inadeni usiitumie",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0787-406-889 UKIWA TAYARI KUJIUNGA",
        "Congratulations! Your CV has passed. You can get 5,000,000TZS in a day. for details: wa.me/2550782435667",
        "Basi iyo hela nitumie kwenye namba hii 0787-406-889 jina litakuja (ABDALLAH MWANAKU) ile namba usitumie laini inamatatizo.",

        "au iyo ela nitumie kwenye m-pesa hii 0788542784 Jina litoke 0788542784.",
        "We need urgently Need Staff salary 4,000,000TZS. Reach HR team at: wa.me/255.",

        "Tumia namba hii ya airtel  kutuma hiyo pesa jina Magomba Maila",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA JENEROZA ROCK BENEDICTO NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "Utanitumia kwenye ii 0750335946  jina  namba yangu inadeni usiitumie",

        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0784862618 au 0784862618",
        "We need urgently Need Staff salary 2,000,000TZS. Reach HR team at: wa.me/2550716484506.",
        "Basi iyo hela nitumie kwenye namba hii 0784862618 jina litakuja (PEREGIA FILIPO) ile namba usitumie laini inamatatizo.",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0786543210 au 0786543210",

        "Au nitumie kwenye HaloPesa Namba.0699137921 jina litakuja ",
        "Congratulations! Your CV has passed. You can get 170,000TZS in a day. for details: wa.me/2550788542784",

        "Mpigie Mzee RAMATUNGU kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga ",

        "MZEE PEREGIA FILIPO tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0617488472)(0617488472)"

        "mjukuu wangu utafuta ji wako mgumu Hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. ",
        ", No need to go out work, just at home to earn 1,500,000TZS a day, please contact us: https://wa.me/2550617488472",
        "TUMIA NAMBA HII (0689592818)KUNITUMIA IYO HELA JINA LITAONYESHA (LINUSI MALALO)",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By JENEROZA ROCK BENEDICTO,ni grp member",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ABDALLAH MWANAKU,ni grp member",
        "TUMIA NAMBA HII (0716484506)KUNITUMIA IYO HELA JINA LITAONYESHA (RAMATUNGU)",

        "We need urgently Need Staff salary 120000TZS. Reach HR team at: wa.me/2550750335946.",
        "tuma kwenye namba hii ya HaloPesa  jina litakuja ABDALLAH MWANAKU Ukituma unijulishe",
        "We need urgently Need Staff salary 6,000,000TZS. Reach HR team at: wa.me/255.",

        "Utanitumia kwa hîi  0696530433 j'ina ni HOSEA MKUMBUKWA.",
        "IYO PESA ITUME KWENYE NAMBA HII 0657538690 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA, ASANTE",
        "666,KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA, KILIMO,UFUGAJI,MACHI MBO,MICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0747878264 AU 0747878264",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0773409724",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",
        "Naomba unitumie iyo Hela kwenye namba hii ya Halotel . jina (PEREGIA FILIPO)",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALI,PESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA  au ",

        "Tumia namba hii ya halotel 0698018072 kutuma hiyo Hela jina JENEROZA ROCK BENEDICTO",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0788542784 UKIWA TAYARI KUJIUNGA",

        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA Halotel NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",

        "Iyo ela tuma humu kwenye   Jina lije Magomba Maila.",
        "Basi iyo hela nitumie kwenye namba hii 0788542784 jina litakuja (Magomba Maila) ile namba usitumie laini inamatatizo.",

        " UT2I Imethibitishwa namba yako ya 065 ... imeshinda Tsh10,000,000.00/=million kutoka Tuzo point ilikupokea pesa yako piga  Asante",
        "TUZO POINT hongera umepata zawadi Sh170,000 milioni kutoka (TUZO POINT) piga sim,.0695567435 kupata zawadi  asante",
        "Au nitumie kwenye pesa Namba.0782734560 jina litakuja ",
        "Utanitumia kwa hîi AIRTEL 0615810764 j'ina ni .",

        "au iyo ela nitumie kwenye pesa hii  Jina litoke .",
        "au iyo ela nitumie kwenye m-pesa hii 0698018072 Jina litoke 0698018072.",

        "Habari. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "ela tuma kwa namba hii 0657666983 jina JUMANNE YASINI MASAKA",

        "TUMIA NAMBA HII (0654321098)KUNITUMIA IYO HELA JINA LITAONYESHA (OLIVA MATIAS)",
        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "hela tuma kwa namba hii 0696530433 jina MWANAIDI KHAMISI",
        "Utanitumia. kwemye namba 0788542784 ya HALOTEL jina NASHONI MBIRIBI.",
        "Naomba unitumie iyo ela kwenye namba hii ya Airtel 0657538690. jina (LINUSI MALALO)",
        "Habari za siku. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA ",
        "Mpigie Mzee JENEROZA ROCK BENEDICTO kwa tiba asili miliki mali,utajiri pete,kazi,kesi,masomo mapenzi,kilimo,ufugaji,biashara Piga 0696530433",
        "Utanitumia kwenye ii 0716484506 airtel jina  namba yangu inadeni usiitumie",

        "Nitumie tu kwenye hii  0689592818 jina HOSEA MKUMBUKWA.",

        "hela tuma kwa namba hii  jina LINUSI MALALO",
        "Tumia namba hii ya AIRTEL 0657538690 kutuma hiyo pesa jina Ester kalobelo",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0788542784",

        "Tumia namba hii ya HALOTEL 0676584303 kutuma hiyo hela jina ",
        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0654321098 AU 0654321098",
        "Mpigie Mzee NASHONI MBIRIBI kwa tiba asili miliki maliutajiri petekazikesimasomo mapenzikilimoufugajibiashara Piga 0787-406-889",
        "TUZO POINT hongera umepata zawadi Sh4000000 milioni kutoka (TUZO POINT) piga sim.0788542784 kupata zawadi  asante",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Tuzo point hongera umepata zawadi Sh170000 milioni kutoka (Tuzo point) piga sim. kupata zawadi  asante",
        "Utanitumia kwa hîi   j'ina ni PEREGIA FILIPO.",

        "Iyo Hela itume humu kwenye halotel 0689592818 jina lije .",

        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By SAID MTAALAM ni grp member",
        "Iyo ela tuma humu kwenye AIRTEL 0755896103 Jina lije NASHONI MBIRIBI.",
        "au iyo ela nitumie kwenye pesa hii 0782734560 Jina litoke 0782734560.",
        "Au nitumie kwenye HaloPesa Namba.0698018072 jina litakuja ABDALLAH MWANAKU",

        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0696530433",
        "MZEE SALOME KALUNGA tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga (0657666983)(0657666983)",
        "Congratulations! Your CV has passed. You can get 4000000TZS in a day. for details: wa.me/2550773409724",
        "Tumia namba hii ya airtel  kutuma hiyo ela jina ",

        "Tumia namba hii ya airtel  kutuma hiyo hela jina LINUSI MALALO",
        "Au nitumie kwenye M-Pesa Namba. jina litakuja MWANAIDI KHAMISI",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",
        "Tumia namba hii ya halotel 0654321098 kutuma hiyo ela jina JENEROZA ROCK BENEDICTO",
        " No need to go out work just at home to earn 6000000TZS a day please contact us: https://wa.me/2550657666983",
        "(666)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJIONGEA NA WAKALA WETU:0755896103",

        "Congratulations! Your CV has passed. You can get 2000000TZS in a day. for details: wa.me/255",
        "Tumia namba hii ya  0786543210 kutuma hiyo pesa jina PEREGIA FILIPO",

        "Nitumie tu kwenye hii HALOTEL 0716484506 jina JENEROZA ROCK BENEDICTO.",
        "mjukuu wangu utafuta ji wako mgumu hela hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0716484506",
        "Basi iyo hela nitumie kwenye namba hii 0698018072 jina litakuja (HOSEA MKUMBUKWA) ile namba usitumie laini inamatatizo.",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALIPESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0781476081 au 0781476081",
        "IYO PESA ITUME KWENYE NAMBA HII 0654321098 JINA ITALETA OLIVA MATIAS NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",
        "Utanitumia kwa hîi  0657666983 j'ina ni .",
        "au iyo ela nitumie kwenye m-pesa hii 0755896103 Jina litoke 0755896103.",
        "au iyo ela nitumie kwenye pesa hii 0617488472 Jina litoke 0617488472.",
        " No need to go out work just at home to earn 1500000TZS a day please contact us: https://wa.me/2550657666983",
        "voda 1XNJ Imethibitishwa namba yako ya 078 ... imeshinda Tsh170000.00/=million kutoka TUZO  POINTI ilikupokea Pesa yako piga 0782734560 Asante",
        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya voda. Mbona kimya na siku zinazidi kwenda...?",

        "Nitumie tu kwenye hii airtel 0750335946 jina Ester kalobelo.",
        "tuma kwenye namba hii ya M-Pesa 0698018072 jina litakuja RAMATUNGU Ukituma unijulishe",

        "Tumia namba hii ya AIRTEL 0750335946 kutuma hiyo ela jina Magomba Maila",
        "Congratulations! Your CV has passed. You can get 6000000TZS in a day. for details: wa.me/2550654321098",
        "au iyo ela nitumie kwenye pesa hii 0782734560 Jina litoke 0782734560.",

        "Habari za mda huu. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        "Utanitumia kwa hîi voda  j'ina ni JUMANNE YASINI MASAKA.",

        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0696530433 AU 0696530433",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0716484506 UKIWA TAYARI KUJIUNGA",
        "Nitumie tu kwenye hii   jina HOSEA MKUMBUKWA.",
        "ela tuma kwa namba hii 0654321098 jina ",
        "Iyo Pesa itume humu kwenye  0676584303 jina lije OLIVA MATIAS.",
        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya airtel. Mbona kimya na siku zinazidi kwenda...?",
        "Basi iyo hela nitumie kwenye namba hii 0716484506 jina litakuja (Magomba Maila) ile namba usitumie laini inamatatizo.",
        "IYO PESA ITUME KWENYE NAMBA HII 0698018072 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",
        "Iyo ela tuma humu kwenye  0716484506 Jina lije LINUSI MALALO.",

        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA HALOTEL NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "Naomba unitumie iyo ela kwenye namba hii ya Halotel 0787-406-889. jina (MWANAIDI KHAMISI)",
        "Basi iyo hela nitumie kwenye namba hii  jina litakuja (SALOME KALUNGA) ile namba usitumie laini inamatatizo.",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",

        "Pesa tuma kwa namba hii 0695567435 jina ",
        "Mpigie Mzee RAMATUNGU kwa tiba asili miliki maliutajiri petekazikesimasomo mapenzikilimoufugajibiashara Piga 0657666983",
        "We need urgently Need Staff salary 170000TZS. Reach HR team at: wa.me/2550676584303.",
        "IYO PESA ITUME KWENYE NAMBA HII 0784862618 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",

        "Utanitumia. kwemye namba 0755896103 ya Halotel jina Magomba Maila.",
        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0733822240 UKIWA TAYARI KUJIUNGA",

        "Utanitumia kwenye ii 0787-406-889 HALOTEL jina JENEROZA ROCK BENEDICTO namba yangu inadeni usiitumie",

        "Habari za mda huumimi hii namba yangu ya HALOTEL.Vp mbona shem  anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",
        " No need to go out work just at home to earn 2000000TZS a day please contact us: https://wa.me/2550676584303"

        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Tumia namba hii ya  0784862618 kutuma hiyo ela jina Magomba Maila",
        "Utanitumia kwenye ii 0786543210  jina SALOME KALUNGA namba yangu inadeni usiitumie",
        "(666)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJIONGEA NA WAKALA WETU:0657666983",
        "Iyo ela tuma humu kwenye  0747878264 Jina lije ",
        "Iyo Hela itume humu kwenye HALOTEL 0733822240 jina lije ABDALLAH MWANAKU.",
        "MPIGIE MZEE  WA TIBA ASILI. MALI. PETE. NYOTA. UZAZI. KUPANDISHWA CHEO KAZINI. KULUDISHA MALI ILIYOPOTEA. NAMBA 0699137921",

        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0786543210 AU 0786543210",
        "Mpigie Mzee NASHONI MBIRIBI kwa tiba asili miliki maliutajiri petekazikesimasomo mapenzikilimoufugajibiashara Piga 0698018072",
        "Au nitumie kwenye M-Pesa Namba.0617488472 jina litakuja PEREGIA FILIPO",
        "Tumia namba hii ya  0699137921 kutuma hiyo hela jina SAID MTAALAM ",
        "Habari za mchana. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",
        "Utanitumia kwa hîi halotel 0654321098 j'ina ni .",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",
        "au iyo ela nitumie kwenye m-pesa hii  Jina litoke .",

        "Utanitumia kwenye ii 0615810764  jina PEREGIA FILIPO namba yangu inadeni usiitumie",
        "Basi iyo hela nitumie kwenye namba hii 0617488472 jina litakuja () ile namba usitumie laini inamatatizo.",
        "voda OZX7 Imethibitishwa namba yako ya 068 ... imeshinda Tsh10000000.00/=million kutoka Tuzo point ilikupokea Hela yako piga 0696530433 Asante",

        "IYO PESA ITUME KWENYE NAMBA HII 0773409724 JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",

        "Habari za mchanamimi OLIVA MATIAShii namba yangu ya Airtel.Vp mbona shem OLIVA MATIAS anakupigia hupatikan tatizo mtandao nn?basi mkiwasiliana naomba nijulishe kwenye namba hii kwa meseji simu yangu imekufa maik ndugu yangu.",

        "AIRTEL ZS2Q Imethibitishwa namba yako ya 069 ... imeshinda Tsh2000000.00/=million kutoka Tuzo point ilikupokea Hela yako piga 0733822240 Asante",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA  NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",
        "We need urgently Need Staff salary 5000000TZS. Reach HR team at: wa.me/255.",
        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",

        "Iyo ela tuma humu kwenye   Jina lije MWANAIDI KHAMISI.",

        "(666)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJIONGEA NA WAKALA WETU:",
        " RWR1 Imethibitishwa namba yako ya 061 ... imeshinda Tsh2000000.00/=million kutoka Tuzo Point ilikupokea hela yako piga 0716484506 Asante",
        "MZEE  tiba asili biashala kazi masomo utajili kesi kuludisha mke&mume piga ()()",

        "ela tuma kwa namba hii  jina OLIVA MATIAS",
        "Airtel 8JLS Imethibitishwa namba yako ya 078 ... imeshinda Tsh1500000.00/=million kutoka TUZO POINT ilikupokea Pesa yako piga 0655251448 Asante",
        "Hela tuma kwa namba hii 0689592818 jina MARIAM NDUGAI",
        "Au nitumie kwenye m-pesa Namba.0782734560 jina litakuja MWANAIDI KHAMISI",
        "Nitumie tu kwenye hii  0654321098 jina .",

        "Naomba unitumie iyo hela kwenye namba hii ya  0617488472. jina (LINUSI MALALO)",
        "(666)HABARI EWE MTANZANIA SASA MLANGO UMEFUNGULIWA JIUNGE NAMATAJIRI BILA KUTOA KAFALA YA BINADAM UTAPEWA MTAJIONGEA NA WAKALA WETU:0655251448",
        "Habari za muda. Mimi  mwenye nyumba wako hii namba yangu ya . Mbona kimya na siku zinazidi kwenda...?",

        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0657538690 AU 0657538690",
        " No need to go out work just at home to earn 6000000TZS a day please contact us: https://wa.me/2550676584303",

        "TUZO  POINTI hongera umepata zawadi Sh6000000 milioni kutoka (TUZO  POINTI) piga sim.0755667788 kupata zawadi  asante",
        "Nitumie tu kwenye hii  0696530433 jina ABDALLAH MWANAKU.",
        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG: 0782734560 AU 0782734560",

        "Utanitumia. kwemye namba  ya  jina HOSEA MKUMBUKWA.",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0615810764 UKIWA TAYARI KUJIUNGA",
        "Utanitumia kwenye ii 0782734560  jina FEBU SHADI WILISON namba yangu inadeni usiitumie",
        "Mpigie Mzee JUMANNE YASINI MASAKA kwa tiba asili miliki maliutajiri petekazikesimasomo mapenzikilimoufugajibiashara Piga 0755896103",
        "TUMIA NAMBA HII (0788542784)KUNITUMIA IYO HELA JINA LITAONYESHA (PEREGIA FILIPO)",
        "Xorry nipo xafari nina xhida kwel nakuomba unixaidie sh elfu 9 nitakurefund nikifika plx By ni grp member",
        "We need urgently Need Staff salary 5000000TZS. Reach HR team at: wa.me/2550696530433.",
        "Congratulations! Your CV has passed. You can get 1500000TZS in a day. for details: wa.me/2550698018072",
        "Iyo pesa itume humu kwenye halotel 0695567435 jina lije FEBU SHADI WILISON.",

        "We need urgently Need Staff salary 4000000TZS. Reach HR team at: wa.me/2550786543210.",

        "We need urgently Need Staff salary 4000000TZS. Reach HR team at: wa.me/2550657538690.",
        "Utanitumia. kwemye namba  ya halotel jina NASHONI MBIRIBI.",
        "mjukuu wangu utafuta ji wako mgumu pesa hazikai mkononi pakazinaisha unasota sana mpenzi hamuelewani je utatunza siri nikikusaidia pesa bila mashaliti magumu nipigie nikwelekeze NO .. 0773409724",
        "TUMIA NAMBA HII ()KUNITUMIA IYO HELA JINA LITAONYESHA ()",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALIPESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0617488472 au 0617488472",
        "tuma kwenye namba hii ya M-Pesa 0699137921 jina litakuja JENEROZA ROCK BENEDICTO Ukituma unijulishe",

        "666KARIBU FREEMASON UTIMIZE NDOTO KATIKA BIASHARA KILIMOUFUGAJIMACHI MBOMICHEZO N.K KWAMHITAJI KUJIUNGA PG:  AU ",
        "hela tuma kwa namba hii 0676584303 jina ",
        "Au nitumie kwenye AirtelMoney Namba.0716484506 jina litakuja FEBU SHADI WILISON",
        "Naomba unitumie iyo Hela kwenye namba hii ya halotel 0615810764. jina ()",
        "tuma kwenye namba hii ya m-pesa 0786543210 jina litakuja MARIAM NDUGAI Ukituma unijulishe",
        "Au nitumie kwenye HaloPesa Namba.0689592818 jina litakuja ",
        "Imethibitishwa namba yako ya 0655251448 imejishindia TSH 5000000 kutoka VODA OFA. Piga 0655251448 ili kupokea hela yako.",
        "Imethibitishwa namba yako ya  imejishindia TSH 120000 kutoka OFA YAKO. Piga  ili kupokea pesa yako.",

        "Mpigie Mzee MARIAM NDUGAI kwa tiba asili miliki maliutajiri petekazikesimasomo mapenzikilimoufugajibiashara Piga 0755667788",
        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALIPESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0755896103 au 0755896103",
        "hela tuma kwa namba hii  jina RAMATUNGU",
        "Mpigie Mzee  kwa tiba asili miliki maliutajiri petekazikesimasomo mapenzikilimoufugajibiashara Piga 0733822240",

        "Iyo ela tuma humu kwenye  0786543210 Jina lije RAMATUNGU",
        "Basi iyo hela nitumie kwenye namba hii 0786543210 jina litakuja (MARIAM NDUGAI) ile namba usitumie laini inamatatizo.",

        "Utanitumia kwa hîi halotel 0716484506 j'ina ni PEREGIA FILIPO.",
        "Utanitumia. kwemye namba  ya  jina .",
        "au iyo ela nitumie kwenye AirtelMoney hii  Jina litoke .",

        "Naomba unitumie iyo hela kwenye namba hii ya Halotel 0773409724. jina ()",
        "Au nitumie kwenye pesa Namba.0654321098 jina litakuja ABDALLAH MWANAKU",
        "Ndugu naomba unitafutie kijana awetandiboi wangu kwenye lori kulekea mikoani   akipatikana nijulishe  analipwa na ofisi zetu kampuni azam awe muaminifu",

        "Habari za asubuhi. Mimi  mwenye nyumba wako hii namba yangu ya voda. Mbona kimya na siku zinazidi kwenda...?",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0676584303 UKIWA TAYARI KUJIUNGA",
        "Congratulations! Your CV has passed. You can get 6000000TZS in a day. for details: wa.me/2550788542784",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0784862618 UKIWA TAYARI KUJIUNGA",

        " No need to go out work just at home to earn 2000000TZS a day please contact us: https://wa.me/2550615810764",
        "Samahani naomba itume kwenye  0716484506 PEREGIA FILIPO.",

        "KARIBU UJIUNGE NA CHAMA CHA (666)FREE'MASON UBADILISHE MAISHA YAKO.MILIKI MALIPESA(UTAJIRI) MAJUMBA NA MAGARI BILA KAFALA PIGA 0615810764 au 0615810764",

        "au iyo ela nitumie kwenye AirtelMoney hii 0782734560 Jina litoke 0782734560.",

        "0787-406-889 Jina litakuja  Nitumie kwenye hiyo ",

        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU  UKIWA TAYARI KUJIUNGA",
        "FRIIMASON TIMIZA NDOTO KUMILIKI PESA MAJUMBA NA MAGARI YA KIFAHARI PIA KUZA BIASHARA VIPAJI NYOTA NA PETE. TUPIGIE SIMU 0716484506 UKIWA TAYARI KUJIUNGA",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
        "VODA OFA hongera umepata zawadi Sh6000000 milioni kutoka (VODA OFA) piga sim.0698018072 kupata zawadi  asante",

        "Mjukuu wangu ndagu niliyokukabizi hiyo uwe makini na pesa hizo zinazokuja usiogope ndio mafanikio yako si nilikwambia utafanikiwa kwa mda mfupi sasa umeona mwenyewe na siri hiyo usitowe kwa mtu yoyote utajili huo ni mkubwa sana utaweza kuweka miladi ya kira aina popote pale unipigie nikuelekeze.",
        "Hela tuma kwa namba hii 0788542784 jina OLIVA MATIAS",
        "TUZO POINT hongera umepata zawadi Sh2000000 milioni kutoka (TUZO POINT) piga sim.0747878264 kupata zawadi  asante",
        "Au nitumie kwenye m-pesa Namba. jina litakuja ABDALLAH MWANAKU",
        "IYO PESA ITUME KWENYE NAMBA HII 0755896103 JINA ITALETA Magomba Maila NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",
        "Imethibitishwa namba yako ya 0784862618 imejishindia TSH 2000000 kutoka Tuzo Point. Piga 0784862618 ili kupokea ela yako.",

        "Utanitumia. kwemye namba 0782734560 ya halotel jina .",
        "Iyo pesa itume humu kwenye halotel 0755896103 jina lije PEREGIA FILIPO.",
        "No need to go out work just at home to earn 170000TZS a day please contact us: https://wa.me/2550788542784",
        "Iyo Hela itume humu kwenye AIRTEL 0615810764 jina lije LINUSI MALALO.",

        "halotel 2Z41 Imethibitishwa namba yako ya 078 ... imeshinda Tsh2000000.00/=million kutoka Tuzo Point ilikupokea ela yako piga 0698018072 Asante",

        " Jina litakuja  Nitumie kwenye hiyo ",

        "Tuzo point hongera umepata zawadi Sh1500000 milioni kutoka (Tuzo point) piga sim.0784862618 kupata zawadi  asante",
        "IYO PESA ITUME KWENYE NAMBA HII  JINA ITALETA NIMEAZIMA SIMU KWA WAKALA HAPA LAINI YANGU NATATIZO UPANDE WA KUPOKEA PESA ASANTE",

        "We need urgently Need Staff salary 120000TZS. Reach HR team at: wa.me/2550657538690.",

        "0782734560 Jina litakuja Ester kalobelo Nitumie kwenye hiyo ",
        "Congratulations! Your CV has passed. You can get 2000000TZS in a day. for details: wa.me/2550782734560",
        "0747878264 Jina litakuja SALOME KALUNGA Nitumie kwenye hiyo ",
        "Utanitumia kwenye ii   jina  namba yangu inadeni usiitumie",
        "We need urgently Need Staff salary 2000000TZS. Reach HR team at: wa.me/2550657666983.",
        "HABARI ZAUKO NI MIMI MWENYE NYUMBA WAKO MNA ENDEREAJE APO NYUMBANI IYO NAMBA YANGU MPYA YA  NAKUMBUSHIA KODI YANGU  MANA NAONA KIMYA SANA NAOMBA TUWA SIRIANE",
    ]

# Function to detect phishing in text
def is_phishing_text(text):
    text_lower = re.sub(r'\s+', ' ', text.lower().strip())
    return any(keyword in text_lower for keyword in PHISHING_KEYWORDS)

# Function to extract text from image
def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"Error reading image: {e}")
        return ""

def detect_phishing(messages_df):
    results = []

    for _, row in messages_df.iterrows():
        phishing_detected = False
        reasons = []

        message_text = row.get('message_text', '')

        # Check message body
        if pd.notnull(message_text) and is_phishing_text(message_text):
            phishing_detected = True
            reasons.append("Text-based phishing")

        # Check image if flagged
        if row.get("is_image", False) and pd.notnull(row.get("image_path", None)):
            extracted_text = extract_text_from_image(row["image_path"])
            if is_phishing_text(extracted_text):
                phishing_detected = True
                reasons.append("Image-based phishing")

        results.append({
            "message_id": row["id"],
            "message_body": message_text,
            "sender_id": str(row.get("sender_id")),
            "receiver_id": str(row.get("recipient_id")),
            "is_phishing": phishing_detected,
            "reasons": ", ".join(reasons)
        })

    return pd.DataFrame(results)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def homeView(request):
    response_chats = supabase.table("chats").select("*").execute()
    response_chats_members = supabase.table("chats").select("chat_members").execute()
    response_account = supabase.table("account").select("*").execute()
    response_messages = supabase.table("messages").select("*").execute()
    chats = response_chats.data
    messages = response_messages.data
    accounts = response_account.data
    chat_members = response_chats_members.data
    get_total_chats = len(chats)
    get_total_messages = len(messages)
    
    df_messages = pd.DataFrame(messages)
    results_df_messages = detect_phishing(df_messages)

    results_list_messages = results_df_messages.to_dict(orient="records")
    is_phishing_messages_total = sum(1 for msg in results_list_messages if msg['is_phishing'])
    not_phishing_messages_total = sum(1 for msg in results_list_messages if not msg['is_phishing'])

    templates = "phishingDetector/home.html"
    context = {
        "chats":chats,
        "get_total_chats":get_total_chats,
        "get_total_messages":get_total_messages,
        "chat_members":chat_members,
        "accounts":accounts,
        "is_phishing_messages_total":is_phishing_messages_total,
        "not_phishing_messages_total":not_phishing_messages_total
    }
    return render(request, templates, context)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def chatsView(request):
    response_chats = supabase.table("chats").select("*").execute()
    response_account = supabase.table("account").select("*").execute()
    accounts = response_account.data
    chats = response_chats.data
    templates = "phishingDetector/chats.html"
    context = {
        "chats":chats,
        "accounts":accounts
    }
    return render(request, templates, context)

@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
@login_required(login_url="/authentication/loginView")
def messagesView(request):
    # Get data from Supabase
    response_messages = supabase.table("messages").select("*").execute()
    response_account = supabase.table("account").select("*").execute()
    response_chats = supabase.table("chats").select("*").execute()

    chat_messages = response_messages.data
    accounts = response_account.data
    chats = response_chats.data

    # Run phishing detection
    df = pd.DataFrame(chat_messages)
    results_df = detect_phishing(df)
    results_list = results_df.to_dict(orient="records")

    # Lookups for sender and receiver names
    sender_lookup = {
        str(account["uid"]): f"{account.get('first_name', '')} {account.get('last_name', '')}".strip()
        for account in accounts
    }

    receiver_lookup = {
        str(chat["id"]): chat.get("chat_name", "")
        for chat in chats
    }

    # === Step 1: Fetch realtime data ===
    response = supabase.table("messages").select("*").execute()
    messages = response.data  # List of dicts

    # === Step 2: Convert to DataFrame ===
    df = pd.DataFrame(messages)

    if df.empty:
        print("❌ No data fetched from Supabase.")
        exit()

    # === Step 5: Set CSV path and load existing message IDs ===
    csv_path = os.path.join(settings.BASE_DIR, "message_phishing_detection.csv")

    existing_ids = set()
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_ids = {row["message_id"] for row in reader}

    # === Step 6: Write new rows to CSV ===
    cleaned_keywords = [re.sub(r"\W+", " ", kw.lower()).strip() for kw in PHISHING_KEYWORDS]

    # Function to check for keyword presence
    def contains_phishing_keyword(text):
        clean_text = re.sub(r"\W+", " ", str(text).lower()).strip()
        return any(keyword in clean_text for keyword in cleaned_keywords)
    
    # new_rows = []
    # for _, row in df.iterrows():
    #     message_id = str(row["id"])
    #     if message_id not in existing_ids:
    #         new_rows.append([
    #             message_id,
    #             row.get("message_text", ""),
    #             row.get("sender_id", ""),
    #             row.get("recipient_id", ""),
    #             row.get("is_phishing", 0),
    #             row.get("reasons", "")
    #         ])

    new_rows = []
    for _, row in df.iterrows():
        message_id = str(row["id"])
        if message_id not in existing_ids:
            message_text = row.get("message_text", "")
            # Set phishing flag based on keyword match
            is_phishing = 1 if contains_phishing_keyword(message_text) else 0
            new_rows.append([
                message_id,
                message_text,
                row.get("sender_id", ""),
                row.get("recipient_id", ""),
                is_phishing,
                row.get("reasons", "")
            ])

            if not PhishingDetection.objects.filter(message_id=message_id).exists():
                PhishingDetection.objects.create(
                    message_id=message_id,
                    message_body=message_text,
                    sender=row.get("sender_id", ""),
                    receiver=row.get("recipient_id", ""),
                    is_phishing=bool(is_phishing),
                    reasons=row.get("reasons", "")
                )

    # === Step 7: Append to CSV ===
    write_header = not os.path.exists(csv_path)
    with open(csv_path, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["message_id", "message_text", "sender_id", "recipient_id", "is_phishing", "reasons"])
        writer.writerows(new_rows)

    print(f"✅ Appended {len(new_rows)} new rows to {csv_path}")

    phishing_detections = PhishingDetection.objects.all().order_by("-id")
    return render(request, "phishingDetector/messages.html", {
        "chat_messages": chat_messages,
        "accounts": accounts,
        "chats": chats,
        "results_list": results_list,
        "phishing_detections": phishing_detections
    })

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def settingsView(request):
    users = get_user_model().objects.all()
    form = AuthorizationForm()
    templates = "phishingDetector/settings.html"
    context = {
        "form":form,
        "users":users
    }
    return render(request, templates, context)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def settingsDeleteView(request, user_id):
    if request.method == "POST" and "delete_user_btn" in request.POST:
        user = get_user_model().objects.filter(pk = user_id).first()
        user.delete()
        messages.success(request, f"user was deleted successfully!")
        return redirect("phishingDetector:settingsView")

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def settingsUpdateView(request, user_id):
    if request.method == "POST" and "update_user_btn" in request.POST:
        user = get_object_or_404(get_user_model(), pk = user_id)
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.save()
        messages.success(request, f"User was updated successfully!")
        return redirect("phishingDetector:settingsView")

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def userAuthorizationView(request, user_id):
    if request.method == "POST" and "authorize_user_btn" in request.POST:
        user = get_object_or_404(get_user_model(), pk = user_id)
        form = AuthorizationForm(request.POST or None, instance = user)
        if not Authorization.objects.filter(id = user_id).exists():
            Authorization.objects.create(
                user = user,
                view_dashboard = request.POST.get("view_dashboard"),
                view_message = request.POST.get("view_message"),
                view_chat = request.POST.get("view_chat"),
                view_setting = request.POST.get("view_setting"),
                view_logs = request.POST.get("view_logs"),
            )
            messages.success(request, f"User was authorized successfully!")
            return redirect("phishingDetector:userAuthorizationView", user_id)

        else:
            Authorization.objects.filter(id = user_id).update(
                user = user,
                view_dashboard = request.POST.get("view_dashboard"),
                view_message = request.POST.get("view_message"),
                view_chat = request.POST.get("view_chat"),
                view_setting = request.POST.get("view_setting"),
                view_logs = request.POST.get("view_logs"),
            )
            messages.success(request, f"User was authorized successfully!")
            return redirect("phishingDetector:userAuthorizationView", user_id)
    
    user = get_object_or_404(get_user_model(), pk = user_id)
    get_user = Authorization.objects.filter(user = user).first()
    form = AuthorizationForm(instance = get_user)    
    templates = "phishingDetector/authorization.html"
    context = {
        "user":user,
        "get_user":get_user,
        "form":form
    }
    return render(request, templates, context) 