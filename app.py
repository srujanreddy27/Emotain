from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import os
from collections import defaultdict
import random

app = Flask(__name__)
app.secret_key = 'pn9@xrnp19kbd-m2h9s8@fyjpz@ef7k5b5x3nyupm+_c_4olq+'  # Change this for production
database_url = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    preferred_languages = db.Column(db.String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_languages(self, languages):
        self.preferred_languages = ','.join(languages)

    def get_languages(self):
        return self.preferred_languages.split(',') if self.preferred_languages else []

    @classmethod
    def validate_password(cls, password):
        return len(password) >= 8

# Load emotion model
model_path = os.path.join('static', 'models', 'best_model.h5')
emotion_model = load_model(model_path)
emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Complete recommendation database with web URLs
RECOMMENDATIONS = {
    'english': {
        'happy': {
            'movies': [
                {
                    'title': 'The Intouchables', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTYxNDA3MDQwNl5BMl5BanBnXkFtZTcwNTU4Mzc1Nw@@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1675434/',
                    'language': 'english'
                },
                {
                    'title': 'La La Land', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMzUzNDM2NzM2MV5BMl5BanBnXkFtZTgwNTM3NTg4OTE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt3783958/',
                    'language': 'english'
                },
                {
                    'title': 'The Secret Life of Walter Mitty',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BODYwNDYxNDk1Nl5BMl5BanBnXkFtZTgwOTAwMTk2MDE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0359950/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Don't Stop Me Now - Queen", 
                    'image_url': 'https://thaka.bing.com/th/id/OIP.qpXxCv_fg9CaY0Z2C5hPTQHaHc?rs=1&pid=ImgDetMain',
                    'link': 'https://open.spotify.com/track/7hQJA50XrCWABAu5v6QZ4i',
                    'language': 'english'
                },
                {
                    'title': "Happy - Pharrell Williams",
                    'image_url': 'https://thaka.bing.com/th/id/OIP.S5K6NYQnQ8Uop9KEdfOdLwHaHa?rs=1&pid=ImgDetMain',
                    'link': 'https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH',
                    'language': 'english'
                },
                {
                    'title': "Walking on Sunshine - Katrina and The Waves",
                    'image_url': 'https://thaka.bing.com/th/id/OIP.dulgP93Oou2cwFhtEwlJagAAAA?rs=1&pid=ImgDetMain',
                    'link': 'https://open.spotify.com/track/05wIrZSwuaVWhcv5FfqeH0',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'The Alchemist - Paulo Coelho', 
                    'image_url': 'https://m.media-amazon.com/images/I/71aFt4+OTOL._AC_UF1000,1000_QL80_.jpg',
                    'link': 'https://www.amazon.com/Alchemist-Paulo-Coelho/dp/0062315005',
                    'language': 'english'
                },
                {
                    'title': 'The Little Prince - Antoine de Saint-Exupéry',
                    'image_url': 'https://thaka.bing.com/th/id/OIP.Mkr9xzR253NNWxA3TNY2KgHaJM?rs=1&pid=ImgDetMain',
                    'link': 'https://www.amazon.com/Little-Prince-Antoine-Saint-Exupery/dp/0156012197',
                    'language': 'english'
                },
                {
                    'title': 'The Happiness Project - Gretchen Rubin',
                    'image_url': 'https://m.media-amazon.com/images/I/81ZTIkqHneL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Happiness-Project-Morning-Aristotle-Generally/dp/006158326X',
                    'language': 'english'
                }
            ]
        },
        'sad': {
            'movies': [
                {
                    'title': 'The Pursuit of Happyness', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTQ5NjQ0NDI3NF5BMl5BanBnXkFtZTcwNDI0MjEzMw@@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0454921/',
                    'language': 'english'
                },
                {
                    'title': 'Manchester by the Sea',
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BMTYxMjk0NDg4Ml5BMl5BanBnXkFtZTgwODcyNjA5OTE@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt4034228/',
                    'language': 'english'
                },
                {
                    'title': 'A Star is Born',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNmE5ZmE3OGItNTdlNC00YmMxLWEzNjctYzAwOGQ5ODg0OTI0XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1517451/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Someone Like You - Adele", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/d8/e3/f9/d8e3f9ea-d6fe-9a1b-9f13-109983d3062e/191404113868.png/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/1zwMYTA5nlNjZxYrvBB2pV',
                    'language': 'english'
                },
                {
                    'title': "Hurt - Johnny Cash",
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b273b13eb2ff19372ac491273a06',
                    'link': 'https://open.spotify.com/track/3loFSXVaGQqDStLxJ4Bd0a',
                    'language': 'english'
                },
                {
                    'title': "Everybody Hurts - R.E.M.",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/d4/9c/f6/d49cf63f-a412-5737-9392-1576c297b475/00888072396272.rgb.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/6PypGyiu0Y2lCDBN1XZEnP',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'The Fault in Our Stars - John Green', 
                    'image_url': 'https://m.media-amazon.com/images/I/81a4kCNuH+L._AC_UF1000,1000_QL80_.jpg',
                    'link': 'https://www.amazon.com/Fault-Our-Stars-John-Green/dp/014242417X',
                    'language': 'english'
                },
                {
                    'title': 'A Little Life - Hanya Yanagihara',
                    'image_url': 'https://m.media-amazon.com/images/I/41tZxxXwsVL._SY445_SX342_.jpg',
                    'link': 'https://www.amazon.com/Little-Life-Hanya-Yanagihara/dp/0804172706',
                    'language': 'english'
                },
                {
                    'title': 'The Book Thief - Markus Zusak',
                    'image_url': 'https://m.media-amazon.com/images/I/41RKGjq-XGL._SY445_SX342_.jpg',
                    'link': 'https://www.amazon.com/Book-Thief-Markus-Zusak/dp/0375842209',
                    'language': 'english'
                }
            ]
        },
        'angry': {
            'movies': [
                {
                    'title': 'Fight Club', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMmEzNTkxYjQtZTc0MC00YTVjLTg5ZTEtZWMwOWVlYzY0NWIwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0137523/',
                    'language': 'english'
                },
                {
                    'title': 'John Wick',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTU2NjA1ODgzMF5BMl5BanBnXkFtZTgwMTM2MTI4MjE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt2911666/',
                    'language': 'english'
                },
                {
                    'title': 'Kill Bill: Vol. 1',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNzM3NDFhYTAtYmU5Mi00NGRmLTljYjgtMDkyODQ4MjNkMGY2XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0266697/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Break Stuff - Limp Bizkit", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/54/2c/e5/542ce5e4-b086-c9a8-bef5-5be01b0dd025/06UMGIM01666.rgb.jpg/500x500bb.jpg',
                    'link': ' https://music.apple.com/us/album/break-stuff/1440754472?i=1440754477&uo=4',
                    'language': 'english'
                },
                {
                    'title': "Du Hast - Rammstein",
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b2739b9b36b0e22870b9f542d937',
                    'link': 'https://open.spotify.com/track/5awDvzxWfd53SSrsRZ8pXO',
                    'language': 'english'
                },
                {
                    'title': "Bulls on Parade - Rage Against the Machine",
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b2739d650d0d98caf3f54b842a0b',
                    'link': 'https://open.spotify.com/track/0tZ3mElWcr74OOhKEiNz1x',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'American Psycho - Bret Easton Ellis', 
                    'image_url': 'https://m.media-amazon.com/images/I/41APfGDwwAL._SY445_SX342_.jpg',
                    'link': 'https://www.amazon.com/American-Psycho-Bret-Easton-Ellis/dp/0679735771',
                    'language': 'english'
                },
                {
                    'title': 'Fight Club - Chuck Palahniuk',
                    'image_url': 'https://m.media-amazon.com/images/I/51yjxrIUKiL._SY445_SX342_.jpg',
                    'link': 'https://www.amazon.com/Fight-Club-Chuck-Palahniuk/dp/0393327345',
                    'language': 'english'
                },
                {
                    'title': 'The Girl with the Dragon Tattoo - Stieg Larsson',
                    'image_url': 'https://m.media-amazon.com/images/I/81ErH6RdLpL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Girl-Dragon-Tattoo-Millennium-Book-ebook/dp/B0015DROBO/ref=sr_1_1?crid=8FXNUM3X7667&dib=eyJ2IjoiMSJ9._MlpmkRDW4grNe5LRFgoq-X0dcUXnYm6dxJbgLDfyFsqrGggtBdrttX1eahuT0cBtQWkJt0b0mFDuju1_PzlRTkZ9aaf9f3sav4ipySTeLrbSj7-sWpJjdoHq2ZS_W_wLEZg2kZwAXrL8z6IKffL6orcrp4_LsLmSDAVS-yIhwc-VCuRyg_bW1BfAuZFGdspwPTx4WLtfOfkHjLDISrjRnJYURv3m_n1zKJxFtmLqUU.5onOKQhyvrEx7P-WAtD_dqW6Wjy-BujOhiFH8ikKG2k&dib_tag=se&keywords=The+Girl+with+the+Dragon+Tattoo+-+Stieg+Larsson&qid=1746257156&s=digital-text&sprefix=the+girl+with+the+dragon+tattoo+-+stieg+larsson%2Cdigital-text%2C3824&sr=1-1',
                    'language': 'english'
                }
            ]
        },
        'disgust': {
            'movies': [
                {
                    'title': 'Requiem for a Dream', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BOTdiNzJlOWUtNWMwNS00NmFlLWI0YTEtZmI3YjIzZWUyY2Y3XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0180093/',
                    'language': 'english'
                },
                {
                    'title': 'Black Swan',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNzY2NzI4OTE5MF5BMl5BanBnXkFtZTcwMjMyNDY4Mw@@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0947798/',
                    'language': 'english'
                },
                {
                    'title': 'The Human Centipede',
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BMTY4Nzk3NzYxOF5BMl5BanBnXkFtZTcwODQwNjQzMw@@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt1467304/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Unwell - Matchbox Twenty", 
                    'image_url': ' https://is1-ssl.mzstatic.com/image/thumb/Music114/v4/ea/35/a1/ea35a127-b30c-0c76-941a-16db9757bea6/075679958501.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/unwell/580697906?i=580698089&uo=4',
                    'language': 'english'
                },
                {
                    'title': "Boulevard of Broken Dreams - Green Day",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music/f2/be/03/mzi.uxygrgff.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/5GorCbAP4aL0EJ16frG2hd',
                    'language': 'english'
                },
                {
                    'title': "Creep - Radiohead",
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b2739293c743fa542094336c5e12',
                    'link': 'https://music.apple.com/us/album/creep-radiohead/1550728401?i=1550728409&uo=4',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'The Metamorphosis - Franz Kafka', 
                    'image_url': 'https://m.media-amazon.com/images/I/91GS-r2FwjL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Metamorphosis-Franz-Kafka/dp/0553213695',
                    'language': 'english'
                },
                {
                    'title': 'Naked Lunch - William S. Burroughs',
                    'image_url': 'https://m.media-amazon.com/images/I/71iStmkEGaL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Naked-Lunch-William-S-Burroughs/dp/0802122078/ref=sr_1_1?dib=eyJ2IjoiMSJ9.nraESK-8KunRbWsZoeFkhcPbzwO_q9bkZeCi5GcSjWcMiP4qQTlJDGb07O40AEQ_Psh_Q2sj7XJDK_IfxnOh83g1RKYoBOkaO7amwQz8IXRYBOyA0glRp7BVZWkAQzR2Z8yCtpFV49h9VbHr06AJ-5TMbz_14R49w5vZ-JWForNRReE2JoeMA8PheYNR5SaaLjzO3AKuCsKINqTD62dYH8zHGH31yEbOkOwPA-HtzXM.Ka_yAOBqi9mrmh0HDWXHjl1zB_epvKxHZI-kVdG84S4&dib_tag=se&keywords=Naked+Lunch+-+William+S.+Burroughs&qid=1746257927&sr=8-1',
                    'language': 'english'
                },
                {
                    'title': 'American Psycho - Bret Easton Ellis', 
                    'image_url': 'https://m.media-amazon.com/images/I/41APfGDwwAL._SY445_SX342_.jpg',
                    'link': 'https://www.amazon.com/American-Psycho-Bret-Easton-Ellis/dp/0679735771',
                    'language': 'english'
                }
            ]
        },
        'fear': {
            'movies': [
                {
                    'title': 'Get Out', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMjUxMDQwNjcyNl5BMl5BanBnXkFtZTgwNzcwMzc0MTI@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt5052448/',
                    'language': 'english'
                },
                {
                    'title': 'A Quiet Place',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMjI0MDMzNTQ0M15BMl5BanBnXkFtZTgwMTM5NzM3NDM@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt6644200/',
                    'language': 'english'
                },
                {
                    'title': 'The Conjuring',
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BMTM3NjA1NDMyMV5BMl5BanBnXkFtZTcwMDQzNDMzOQ@@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt1457767/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Thriller - Michael Jackson", 
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b273f6de355783e42c7c357cfc93',
                    'link': 'https://open.spotify.com/track/2LlQb7Uoj1kKyGhlkBf9aC',
                    'language': 'english'
                },
                {
                    'title': "Disturbia - Rihanna",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/2b/c0/81/2bc081c8-25f0-ba43-d451-587a54613778/16UMGIM59202.rgb.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/2VOomzT6VavJOGBeySqaMc',
                    'language': 'english'
                },
                {
                    'title': "Monster - Skillet",
                    'image_url': ' https://is1-ssl.mzstatic.com/image/thumb/Music6/v4/38/af/10/38af10b4-ff1f-879b-e1cc-072367cab8e2/075679951083.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/2UREu1Y8CO4jXkbvqAtP7g',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'The Shining - Stephen King', 
                    'image_url': ' https://is1-ssl.mzstatic.com/image/thumb/Music6/v4/38/af/10/38af10b4-ff1f-879b-e1cc-072367cab8e2/075679951083.jpg/500x500bb.jpg',
                    'link': 'https://www.amazon.com/Shining-Stephen-King/dp/0307743659',
                    'language': 'english'
                },
                {
                    'title': 'It - Stephen King',
                    'image_url': 'https://m.media-amazon.com/images/I/71ZIovNjw+L._SL1500_.jpg',
                    'link': 'https://www.amazon.com/It-Novel-Stephen-King/dp/1501142976',
                    'language': 'english'
                },
                {
                    'title': 'House of Leaves - Mark Z. Danielewski',
                    'image_url': 'https://m.media-amazon.com/images/I/711hUvzvB7L._SL1500_.jpg',
                    'link': 'https://www.amazon.com/House-Leaves-Mark-Z-Danielewski/dp/0375703764',
                    'language': 'english'
                }
            ]
        },
        'neutral': {
            'movies': [
                {
                    'title': 'The Social Network', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BOGUyZDUxZjEtMmIzMC00MzlmLTg4MGItZWJmMzBhZjE0Mjc1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1285016/',
                    'language': 'english'
                },
                {
                    'title': 'Her',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMjA1Nzk0OTM2OF5BMl5BanBnXkFtZTgwNjU2NjEwMDE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1798709/',
                    'language': 'english'
                },
                {
                    'title': 'Lost in Translation',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTI2NDI5ODk4N15BMl5BanBnXkFtZTYwMTI3NTE3._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0335266/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Clair de Lune - Debussy", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/8f/b6/43/8fb6439e-ff30-9a16-9218-093fbe6fa73b/s05.olyuhspr.tif/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/clair-de-lune-debussy/14068868?i=14068866&uo=4',
                    'language': 'english'
                },
                {
                    'title': "River Flows In You - Yiruma",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/27/c3/88/27c38842-4101-73f1-b69e-7bef5795b9b0/859764938339_cover.jpg/500x500bb.jpg',
                    'link': ' https://music.apple.com/us/album/river-flows-in-you-yiruma/1644080798?i=1644080802&uo=4',
                    'language': 'english'
                },
                {
                    'title': "Weightless - Marconi Union",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/c3/3a/d6/c33ad6a3-ec91-62e4-0912-d4a873d4fed0/cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/weightless/571977211?i=571977598&uo=4',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'Sapiens - Yuval Noah Harari', 
                    'image_url': 'https://m.media-amazon.com/images/I/716E6dQ4BXL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Sapiens-Humankind-Yuval-Noah-Harari/dp/0062316095',
                    'language': 'english'
                },
                {
                    'title': 'The Power of Now - Eckhart Tolle',
                    'image_url': 'https://m.media-amazon.com/images/I/61Ij8nLooNL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Power-Now-Guide-Spiritual-Enlightenment/dp/1577314808',
                    'language': 'english'
                },
                {
                    'title': 'Quiet: The Power of Introverts - Susan Cain',
                    'image_url': 'https://m.media-amazon.com/images/I/710KQAE6d5L._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Quiet-Power-Introverts-World-Talking/dp/0307352153',
                    'language': 'english'
                }
            ]
        },
        'surprise': {
            'movies': [
                {
                    'title': 'Inception', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1375666/',
                    'language': 'english'
                },
                {
                    'title': 'The Sixth Sense',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMWM4NTFhYjctNzUyNi00NGMwLTk3NTYtMDIyNTZmMzRlYmQyXkEyXkFqcGdeQXVyMTAwMzUyOTc@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt0167404/',
                    'language': 'english'
                },
                {
                    'title': 'Shutter Island',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BYzhiNDkyNzktNTZmYS00ZTBkLTk2MDAtM2U0YjU1MzgxZjgzXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1130884/',
                    'language': 'english'
                }
            ],
            'music': [
                {
                    'title': "Somebody That I Used To Know - Gotye", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music/v4/9e/25/ef/9e25ef6a-84b7-a1a4-1ed4-08eb28661064/Cover.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/4wCmqSrbyCgxEXROQE6vtV',
                    'language': 'english'
                },
                {
                    'title': "Bittersweet Symphony - The Verve",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music/c7/90/5b/mzi.fjghyghs.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/57iDDD9N9tTWe75x6qhStw',
                    'language': 'english'
                },
                {
                    'title': "Bohemian Rhapsody - Queen",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/ce/5b/fa/ce5bfa48-806d-fd5e-933e-a2c97871cac2/884977631524.jpg/500x500bb.jpg',
                    'link': 'https://open.spotify.com/track/7tFiyTwD0nx5a1eklYtX2J',
                    'language': 'english'
                }
            ],
            'books': [
                {
                    'title': 'Gone Girl - Gillian Flynn', 
                    'image_url': 'https://m.media-amazon.com/images/I/713e4Yk6brL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Gone-Girl-Gillian-Flynn/dp/0307588378',
                    'language': 'english'
                },
                {
                    'title': 'The Girl on the Train - Paula Hawkins',
                    'image_url': 'https://m.media-amazon.com/images/I/713e4Yk6brL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Girl-Train-Paula-Hawkins/dp/1594634025',
                    'language': 'english'
                },
                {
                    'title': 'Sharp Objects - Gillian Flynn',
                    'image_url': 'https://m.media-amazon.com/images/I/71-JO+PSPwL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Sharp-Objects-Novel-Gillian-Flynn/dp/0307341550',
                    'language': 'english'
                }
            ]
        }
    },
    'hindi': {
        'happy': {
            'movies': [
                {
                    'title': '3 Idiots', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNTkyOGVjMGEtNmQzZi00NzFlLTlhOWQtODYyMDc2ZGJmYzFhXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1187043/',
                    'language': 'hindi'
                },
                {
                    'title': 'Yeh Jawaani Hai Deewani',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTgwNjQ4MjY5OV5BMl5BanBnXkFtZTgwMzE4NDMxMTE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt2178470/',
                    'language': 'hindi'
                },
                {
                    'title': 'Zindagi Na Milegi Dobara',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BZGFmMjI2NzMtZDdmYy00NGU5LTgxMmItMGIzMDQ4MDY5NjI5XkEyXkFqcGdeQXVyODE5NzE3OTE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1562872/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Badtameez Dil", 
                    'image_url': 'https://c.saavncdn.com/707/Badtameez-Dil-Hindi-2013-20221204173610-500x500.jpg',
                    'link': 'https://www.jiosaavn.com/song/badtameez-dil/GB8WfS5uZ1Y',
                    'language': 'hindi'
                },
                {
                    'title': "Senorita",
                    'image_url': 'https://c.saavncdn.com/707/Badtameez-Dil-Hindi-2013-20221204173610-500x500.jpg',
                    'link': 'https://www.jiosaavn.com/song/senorita/GB8WfS5uZ1Y',
                    'language': 'hindi'
                },
                {
                    'title': "Gallan Goodiyaan",
                    'image_url': 'https://c.saavncdn.com/707/Badtameez-Dil-Hindi-2013-20221204173610-500x500.jpg',
                    'link': 'https://www.jiosaavn.com/song/gallan-goodiyaan/GB8WfS5uZ1Y',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'Five Point Someone - Chetan Bhagat', 
                    'image_url': 'https://m.media-amazon.com/images/I/71Hn9O6a1EL._AC_UF1000,1000_QL80_.jpg',
                    'link': 'https://www.amazon.com/Five-Point-Someone-Chetan-Bhagat/dp/8129115301',
                    'language': 'hindi'
                },
                {
                    'title': 'The Secret of the Nagas - Amish Tripathi',
                    'image_url': 'https://m.media-amazon.com/images/I/71XPG4uD4NL._AC_UF1000,1000_QL80_.jpg',
                    'link': 'https://www.amazon.com/Secret-Nagas-Shiva-Trilogy/dp/9381626347',
                    'language': 'hindi'
                },
                {
                    'title': 'The Immortals of Meluha - Amish Tripathi',
                    'image_url': 'https://m.media-amazon.com/images/I/71XPG4uD4NL._AC_UF1000,1000_QL80_.jpg',
                    'link': 'https://www.amazon.com/Immortals-Meluha-Shiva-Trilogy/dp/9380658747',
                    'language': 'hindi'
                }
            ]
        },
        'sad': {
            'movies': [
                {
                    'title': 'Kal Ho Naa Ho', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMDNjZmRmMjEtMDA5NS00ZjIxLWJlYWQtNTIyM2FiZjg4NzM4XkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt0347304/',
                    'language': 'hindi'
                },
                {
                    'title': 'Aashiqui 2',
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BN2M2MjQwZmQtMWQ5ZS00NmYwLWEwZmMtZmM1ZWM3MGMzOGU3XkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt2203308/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Tum Hi Ho - Aashiqui 2", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/bb/23/ee/bb23eeed-0c35-4f1d-2b11-485622777ae4/8902894353007_cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/tum-hi-ho/1073359412?i=1073359419&uo=4',
                    'language': 'hindi'
                },
                {
                    'title': "Channa Mereya - Ae Dil Hai Mushkil",
                    'image_url': ' https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/05/ae/75/05ae75b7-0793-291e-f33a-fb874091a11b/886446286020.jpg/500x500bb.jpg',
                    'link': ' https://music.apple.com/us/album/channa-mereya-from-ae-dil-hai-mushkil/1184916598?i=1184917552&uo=4',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'The Ministry of Utmost Happiness - Arundhati Roy', 
                    'image_url': 'https://m.media-amazon.com/images/I/91DFDwX4gvL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Ministry-Utmost-Happiness-novel-ebook/dp/B01NBZXMTT/ref=sr_1_1?dib=eyJ2IjoiMSJ9.PolajPcftKwcfzGGuuv6D07XZGWgCtPbxt5ZqaAhuySj-crq27y_psewGTVPFfNzZyCO7ER5s-SYStSmrHTPA6JN4Mu6580F7-cp97m-_m91hr7vyZ7nKFoKZQLTOUpD_5Lcs1bzMrT3C3FCRKuqa865fhILsn5aucMJNK9yECw6NdC9T_LwqrPhEIbIyis2a_xUjptI_3sseAeJjMeFNjTRRzEmWLtrPHpdmWOIC00.6dwPbgMBxkOqXVSUcUD9hFT-hcCh7-1uF9uON0mUPEM&dib_tag=se&keywords=The+Ministry+of+Utmost+Happiness+-+Arundhati+Roy&qid=1746260200&sr=8-1',
                    'language': 'hindi'
                }
            ]
        },
        'angry': {
            'movies': [
                {
                    'title': 'Gangs of Wasseypur', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTc5NjY4MjUwNF5BMl5BanBnXkFtZTgwODM3NzM5MzE@._V1_FMjpg_UX1000_.jpg',
                    'link': 'https://www.imdb.com/title/tt1954470/',
                    'language': 'hindi'
                },
                {
                    'title': 'Singham',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BYjlkNjdlOGItYjlmNC00ZmM3LWEzZTItYTgxMWUxNmEyYTMyXkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt1948150/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Dilliwaali Girlfriend - Yeh Jawaani Hai Deewani", 
                    'image_url': '  https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/62/d6/74/62d67432-0670-631f-db6a-d4bac3adae4b/8902894353328_cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/dilliwaali-girlfriend/1070912669?i=1070912823&uo=4',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'The White Tiger - Aravind Adiga', 
                    'image_url': 'https://m.media-amazon.com/images/I/71PasGvOcnL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/White-Tiger-Novel-Aravind-Adiga/dp/1416562605',
                    'language': 'hindi'
                }
            ]
        },
        'disgust': {
            'movies': [
                {
                    'title': 'Ugly', 
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BNGExZjhjMWYtYmRmNC00ZmRkLWJmYTYtMjY0YzUzNDcyNzhkXkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt2882328/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Dard Dilo Ke - The Xpose", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music30/v4/33/79/52/3379528c-f776-ee00-5f74-8612065dbe80/8902894355704_cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/dard-dilo-ke/1111673204?i=1111673461&uo=4',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'The Ministry of Utmost Happiness - Arundhati Roy', 
                    'image_url': 'https://m.media-amazon.com/images/I/91DFDwX4gvL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Ministry-Utmost-Happiness-novel-ebook/dp/B01NBZXMTT/ref=sr_1_1?dib=eyJ2IjoiMSJ9.PolajPcftKwcfzGGuuv6D07XZGWgCtPbxt5ZqaAhuySj-crq27y_psewGTVPFfNzZyCO7ER5s-SYStSmrHTPA6JN4Mu6580F7-cp97m-_m91hr7vyZ7nKFoKZQLTOUpD_5Lcs1bzMrT3C3FCRKuqa865fhILsn5aucMJNK9yECw6NdC9T_LwqrPhEIbIyis2a_xUjptI_3sseAeJjMeFNjTRRzEmWLtrPHpdmWOIC00.6dwPbgMBxkOqXVSUcUD9hFT-hcCh7-1uF9uON0mUPEM&dib_tag=se&keywords=The+Ministry+of+Utmost+Happiness+-+Arundhati+Roy&qid=1746260739&sr=8-1',
                    'language': 'hindi'
                }
            ]
        },
        'fear': {
            'movies': [
                {
                    'title': 'Tumbbad', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BOTY0YzY3MTMtOWQ5Yi00ODY2LThhOGMtMzFlMjhlODcxOGU1XkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt8239946/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Bhoot Hoon Main - Ragini MMS 2", 
                    'image_url': ' https://is1-ssl.mzstatic.com/image/thumb/Music128/v4/55/6f/4e/556f4e29-6520-e5b3-51c3-e5d825ecff98/8903431695123_cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/bhoot-hoon-main-from-lupt/1437503551?i=1437503552&uo=4',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'The Devotion of Suspect X - Keigo Higashino', 
                    'image_url': 'https://m.media-amazon.com/images/I/716kh-UcI-L._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Devotion-Suspect-Detective-Galileo-Novel/dp/1250002699/ref=sr_1_1?dib=eyJ2IjoiMSJ9.l_gyHFHWaKaqEDKXis3zjmLyaQtQpDKTRKBQ4rtQD7tKx4G34D2VYsh-c2gcehfdx8k07qlKC4oXuoobQKu7i-M1QW0lgUGGUKXVPgmQ4-sZbGdqqxfdEY-MF87UiMkR0_TCi88MmZdmsYKhiWZeztPVeUZLDxx2J2u6RJynuwLYR9D8b9-nqawYONCOA0fBxwIMedaJEHNnBaYqSDkzQ3XPFfCYcdPUwJsFPVHrGGQ.3RO4oTz91go83uJfJlPh9b4WH1eTYlRuiRLjWLvpJi4&dib_tag=se&keywords=The+Devotion+of+Suspect+X+-+Keigo+Higashino&qid=1746260938&sr=8-1',
                    'language': 'hindi'
                }
            ]
        },
        'neutral': {
            'movies': [
                {
                    'title': 'Piku', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMTUwOTMxNjc2OV5BMl5BanBnXkFtZTgwODQ4OTMxNTE@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt3767372/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Tum Ho - Rockstar", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/b2/fc/80/b2fc80e1-2a07-0ce8-bc85-79b28aae0d80/196100610321.png/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/tum-ho-rockstar/1564225500?i=1564225501&uo=4',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'The Namesake - Jhumpa Lahiri', 
                    'image_url': 'https://m.media-amazon.com/images/I/81g03YqF1QL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Namesake-Jhumpa-Lahiri/dp/0395927218',
                    'language': 'hindi'
                }
            ]
        },
        'surprise': {
            'movies': [
                {
                    'title': 'Andhadhun', 
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BMjZiYTNkNjUtNzI3MC00YWJmLTljM2QtNTI3MTU3ODYzNWFjXkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt8108198/',
                    'language': 'hindi'
                }
            ],
            'music': [
                {
                    'title': "Aankh Marey - Simmba", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/99/4c/e2/994ce25e-0fe1-1287-972d-7ab5f09e55e1/8902894360616_cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/aankh-marey/1447936145?i=1447936149&uo=4',
                    'language': 'hindi'
                }
            ],
            'books': [
                {
                    'title': 'The Silent Patient - Alex Michaelides', 
                    'image_url': 'https://m.media-amazon.com/images/I/91lslnZ-btL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Silent-Patient-Alex-Michaelides/dp/1250301696',
                    'language': 'hindi'
                }
            ]
        }
    },
    'telugu': {
        'happy': {
            'movies': [
                {
                    'title': 'Jathi Ratnalu', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNGFhZjM5MTUtNzZlMy00MmQ2LTg0YjAtM2IzMzFmZDQwNzhmXkEyXkFqcGdeQXVyNjYyOTQ2OTc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt11306376/',
                    'language': 'telugu'
                },
                {
                    'title': 'Majili',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BYThlYzllMzEtYmUxZi00ZDA1LTgwNjAtODdmNGFhNGQzYWM4XkEyXkFqcGc@._V1_SX300.jpg',
                    'link': ' https://www.imdb.com/title/tt8737614/',
                    'language': 'telugu'
                },
                {
                    'title': 'Fidaa',
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BYTZjYjhlZTMtYzg1OC00OWYwLThhNGEtY2M2MmNjM2FmMzhiXkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt7159382/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Butta Bomma - Ala Vaikunthapurramuloo", 
                    'image_url': ' https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/46/aa/48/46aa4863-c1ec-4574-e98e-80b8c1f3ef69/cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/butta-bomma-remix-from-ala-vaikunthapurramuloo/1736706821?i=1736707044&uo=4',
                    'language': 'telugu'
                },
                {
                    'title': "Samajavaragamana - Ala Vaikunthapurramuloo",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music123/v4/46/14/df/4614df1c-3f61-6bf5-5c3e-ee304895cfca/cover.jpg/500x500bb.jpg',
                    'link': ' https://music.apple.com/us/album/samajavaragamana/1493907854?i=1493907867&uo=4',
                    'language': 'telugu'
                },
                {
                    'title': "Seeti Maar - DJ",
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music117/v4/4f/f3/36/4ff33640-03e6-f00c-8725-8dd639f009ca/cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/seeti-maar/1247180103?i=1247180141&uo=4',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'Asura: Tale of the Vanquished - Anand Neelakantan', 
                    'image_url': 'https://m.media-amazon.com/images/I/91rvw+ezAiL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Asura-Vanquished-Story-Ravana-People/dp/B07WP68X7X/ref=sr_1_1?dib=eyJ2IjoiMSJ9.Ub68dXU25UWLJ83svT6PRB-5waZT5dz-6ItByAPfM5hfH_taUjgnRer8NbZAue2iKU3Mw_BChGksmhV0D_QIuw.yzdofOhRtk5YzY1YKJhxif1UKhG_kFCqZqL5iXIXTC4&dib_tag=se&keywords=Asura%3A+Tale+of+the+Vanquished+-+Anand+Neelakantan&qid=1746261551&sr=8-1',
                    'language': 'telugu'
                },
                {
                    'title': 'The White Tiger - Aravind Adiga',
                    'image_url': 'https://m.media-amazon.com/images/I/81crp4tmxAL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/The-White-Tiger-Aravind-Adiga-audiobook/dp/B0018O22X0/ref=sr_1_1?crid=3V1BFQ7X377ZH&dib=eyJ2IjoiMSJ9.ESXbZQea0RovR09L9UuHH2EUDRDTZLur6u0IP7CbkJw.1HoUwR_IKLZuewmU2UyqAyh5dso-SilgioB_M0tySHc&dib_tag=se&keywords=The+White+Tiger+-+Aravind+Adiga&qid=1746261600&s=audible&sprefix=asura+tale+of+the+vanquished+-+anand+neelakantan%2Caudible%2C675&sr=1-1',
                    'language': 'telugu'
                }
            ]
        },
        'sad': {
            'movies': [
                {
                    'title': 'Arjun Reddy', 
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BY2Y4ZDhmM2UtMWY0ZS00ODFmLTk2N2YtMDM1ZmQzYWI4ZDQ3XkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt7294534/',
                    'language': 'telugu'
                },
                {
                    'title': 'Ninnu Kori',
                    'image_url': 'https://thaka.bing.com/th/id/OIP.vrwYFqC3DUB-jz9itHL8xAHaKX?w=126&h=180&c=7&r=0&o=7&cb=iwp1&dpr=1.1&pid=1.7&rm=3',
                    'link': 'https://www.imdb.com/title/tt6996016/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Emai Poyave - Dear Comrade", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music113/v4/e8/a3/0f/e8a30fb6-53cb-7d7e-0bc9-d958cdf211e1/8903431775429_cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/yetu-pone-from-dear-comrade/1513207654?i=1513207656&uo=4',
                    'language': 'telugu'
                },
                {
                    'title': "Evarini Adaganu - Sita Ramam",
                    'image_url': 'https://thaka.bing.com/th/id/OIP.l-SxfmjuMqlYaHMkpXRQogHaEK?w=282&h=180&c=7&r=0&o=5&dpr=1.1&pid=1.7',
                    'link': 'https://music.apple.com/us/album/yevarini-adaganu/1644086776?i=1644087311&uo=4',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'The Ministry of Utmost Happiness - Arundhati Roy', 
                    'image_url': 'https://m.media-amazon.com/images/I/91DFDwX4gvL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Ministry-Utmost-Happiness-novel-ebook/dp/B01NBZXMTT/ref=sr_1_1?dib=eyJ2IjoiMSJ9.PolajPcftKwcfzGGuuv6D07XZGWgCtPbxt5ZqaAhuySj-crq27y_psewGTVPFfNzZyCO7ER5s-SYStSmrHTPA6JN4Mu6580F7-cp97m-_m91hr7vyZ7nKFoKZQLTOUpD_5Lcs1bzMrT3C3FCRKuqa865fhILsn5aucMJNK9yECw6NdC9T_LwqrPhEIbIyis2a_xUjptI_3sseAeJjMeFNjTRRzEmWLtrPHpdmWOIC00.6dwPbgMBxkOqXVSUcUD9hFT-hcCh7-1uF9uON0mUPEM&dib_tag=se&keywords=The+Ministry+of+Utmost+Happiness+-+Arundhati+Roy&qid=1746262300&sr=8-1',
                    'language': 'telugu'
                }
            ]
        },
        'angry': {
            'movies': [
                {
                    'title': 'Rangasthalam', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMjQxNjg4ZGUtNzViNS00Y2Q3LTlkOTUtZDFlNjc5NjE3Njc2XkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt7392212/',
                    'language': 'telugu'
                },
                {
                    'title': 'Baahubali: The Beginning',
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BM2YxZThhZmEtYzM0Yi00OWYxLWI4NGYtM2Y2ZDNmOGE0ZWQzXkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt2631186/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Dandaalayyaa - Bahubali-2", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/f6/bd/05/f6bd057f-f78d-42a8-d86a-eb8a5a4c8c21/dj.cqcxdayj.jpg/500x500bb.jpg',
                    'link': ' https://music.apple.com/us/album/dandaalayyaa/1219281887?i=1219281907&uo=4',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'The White Tiger - Aravind Adiga', 
                    'image_url': 'https://m.media-amazon.com/images/I/71PasGvOcnL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/White-Tiger-Novel-Aravind-Adiga/dp/1416562605',
                    'language': 'telugu'
                }
            ]
        },
        'disgust': {
            'movies': [
                {
                    'title': 'Evaru', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BOGUzNDdmYjItOWRhYS00YTlmLTgwMWYtMWRmODc0ODNlZWZjXkEyXkFqcGc@._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt10545484/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Nee Kannu Neeli Samudram - Uppena", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/08/5f/90/085f9021-b2d4-cd8d-1a3e-35e24db23fc3/cover.jpg/500x500bb.jpg',
                    'link': 'https://music.apple.com/us/album/nee-kannu-neeli-samudram-from-uppena/1501175767?i=1501175770&uo=4',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'The Ministry of Utmost Happiness - Arundhati Roy', 
                    'image_url': 'https://m.media-amazon.com/images/I/91DFDwX4gvL._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Ministry-Utmost-Happiness-novel-ebook/dp/B01NBZXMTT/ref=sr_1_1?dib=eyJ2IjoiMSJ9.PolajPcftKwcfzGGuuv6D07XZGWgCtPbxt5ZqaAhuySj-crq27y_psewGTVPFfNzZyCO7ER5s-SYStSmrHTPA6JN4Mu6580F7-cp97m-_m91hr7vyZ7nKFoKZQLTOUpD_5Lcs1bzMrT3C3FCRKuqa865fhILsn5aucMJNK9yECw6NdC9T_LwqrPhEIbIyis2a_xUjptI_3sseAeJjMeFNjTRRzEmWLtrPHpdmWOIC00.6dwPbgMBxkOqXVSUcUD9hFT-hcCh7-1uF9uON0mUPEM&dib_tag=se&keywords=The+Ministry+of+Utmost+Happiness+-+Arundhati+Roy&qid=1746260200&sr=8-1',
                    'language': 'hindi'
                }
            ]
        },
        'fear': {
            'movies': [
                {
                    'title': 'Awe', 
                    'image_url': ' https://m.media-amazon.com/images/M/MV5BMDdmNzJmNmQtMzBlYS00NDhkLTgyMTUtYTI5MWQzOGFlYjFhXkEyXkFqcGdeQXVyMTAyMzYwNzgw._V1_SX300.jpg',
                    'link': 'https://www.imdb.com/title/tt10291806/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Bhayam Bhayam - Awe", 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music122/v4/71/d4/7b/71d47b1d-a3fc-1d44-62b6-35fdac078923/cover.jpg/500x500bb.jpg',
                    'link': ' https://music.apple.com/us/album/bhayam-bhayam/1215236857?i=1215237130&uo=4',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'The Devotion of Suspect X - Keigo Higashino', 
                    'image_url': 'https://m.media-amazon.com/images/I/716kh-UcI-L._SL1500_.jpg',
                    'link': 'https://www.amazon.com/Devotion-Suspect-Detective-Galileo-Novel/dp/1250002699/ref=sr_1_1?dib=eyJ2IjoiMSJ9.l_gyHFHWaKaqEDKXis3zjmLyaQtQpDKTRKBQ4rtQD7tKx4G34D2VYsh-c2gcehfdx8k07qlKC4oXuoobQKu7i-M1QW0lgUGGUKXVPgmQ4-sZbGdqqxfdEY-MF87UiMkR0_TCi88MmZdmsYKhiWZeztPVeUZLDxx2J2u6RJynuwLYR9D8b9-nqawYONCOA0fBxwIMedaJEHNnBaYqSDkzQ3XPFfCYcdPUwJsFPVHrGGQ.3RO4oTz91go83uJfJlPh9b4WH1eTYlRuiRLjWLvpJi4&dib_tag=se&keywords=The+Devotion+of+Suspect+X+-+Keigo+Higashino&qid=1746262925&sr=8-1',
                    'language': 'telugu'
                }
            ]
        },
        'neutral': {
            'movies': [
                {
                    'title': 'C/o Kancharapalem', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BZjYyM2UwMGQtMjI4YS00Y2U4LTllOWItYjIzODlhZThlMDc2XkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                    'link': 'https://www.imdb.com/title/tt7391996/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Vellipomaakey - Sahasam Swasaga Sagipo", 
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b2733dccac8b6e55f46b0f9d362f',
                    'link': 'https://open.spotify.com/track/6KGhNDNqcjRZlRJ0xizRO2',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'The Namesake - Jhumpa Lahiri', 
                    'image_url': 'https://a.media-amazon.com/images/I/71t19fqA5SL.SL1154.jpg',
                    'link': 'https://www.amazon.in/Namesake-Jhumpa-Lahiri/dp/0007258917',
                    'language': 'telugu'
                }
            ]
        },
        'surprise': {
            'movies': [
                {
                    'title': 'Kshanam', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BYmRlMmZjOWItZjgzZS00Mjc4LWEwZWYtZTA3YWZkMjgzY2JkXkEyXkFqcGc@.V1.jpg',
                    'link': 'https://www.imdb.com/title/tt5504168/',
                    'language': 'telugu'
                }
            ],
            'music': [
                {
                    'title': "Oosupodu ", 
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b273b86bd3f91106fe04bc03d32b',
                    'link': 'https://open.spotify.com/track/3K8KLno4fDcBvBLiYAzVWf',
                    'language': 'telugu'
                }
            ],
            'books': [
                {
                    'title': 'The Silent Patient - Alex Michaelides', 
                    'image_url': 'https://a.media-amazon.com/images/I/41bsvxNUSdL.SY445_SX342.jpg',
                    'link': 'https://www.amazon.in/Silent-Patient-Alex-Michaelides/dp/1250301696',
                    'language': 'telugu'
                }
            ]
        }
    },
    'tamil': {
    'happy': {
        'movies': [
            {
                'title': 'Sivaji: The Boss',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPmKZ6gwvMmu1qv9zYSPY8OvZAH9zML29bbeLAqNj8LAUXRKZlH6ntIzqH-CtyKZeNxAqdgQ',
                'link': 'https://www.imdb.com/title/tt0479751/?ref_=fn_all_ttl_1',
                'language': 'tamil'
            },
            {
                'title': 'Muthu',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTiBW5zJozRWokbf3HHk4GPX-L4qBhPo82538MSlnJvtKtWgSTswqqJYFZC98b-ngq1rTiNQg',
                'link': 'https://www.imdb.com/title/tt0140399/?ref_=fn_all_ttl_1',
                'language': 'tamil'
            },
            {
                'title': 'Nanban',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ9R2BkQn1sy_PDwDF7_78ROKbdHnuEFxpACoNtuXQGMgTI8ANj2m7i5HpZzXE5I5OV2Evw6w',
                'link': 'https://www.imdb.com/title/tt2180477/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Why This Kolaveri Di - 3",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b2732fb9cbc9a24d3bfd090678c3',
                'link': 'https://open.spotify.com/track/5UEBvJVvaNaRKkL1ZXDudJ',
                'language': 'tamil'
            },
            {
                'title': "Adiye - Bachelor",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b27399e9e5a108d4a457de95e016',
                'link': 'https://open.spotify.com/album/1vPj6t2spMcJkrtlDsFaC8',
                'language': 'tamil'
            },
            {
                'title': "Vaathi Coming - Master",
                'image_url': 'https://i.scdn.co/image/ab67616d00001e02b6a0a2631cc3de08fa8845b2',
                'link': 'https://open.spotify.com/album/0SOw7gw33kUZHgyZpLY1Jh',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Ponniyin Selvan - Kalki Krishnamurthy',
                'image_url': 'https://a.media-amazon.com/images/I/71J4aHuWLqL.SY466.jpg',
                'link': 'https://www.amazon.in/Ponniyin-Selvan-5-Set-Kalki/dp/9382578382',
                'language': 'tamil'
            },
            {
                'title': 'Payanigal Kavanikkavum - Balakumaran',
                'image_url': 'https://a.media-amazon.com/images/I/A16Wgyg54wL.SL1500.jpg',
                'link': 'https://www.amazon.in/Payanigal-Kavanikkavum-Balakumaran/dp/B00HR1U35W',
                'language': 'tamil'
            }
        ]
    },
    'sad': {
        'movies': [
            {
                'title': 'Kaakha Kaakha',
                'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/69/Kaakha_Kaakha_poster.jpg',
                'link': 'https://www.imdb.com/title/tt0375878/',
                'language': 'tamil'
            },
            {
                'title': 'Varanam Aayiram',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR2LivPw94_xNP-4eFfUPkJI6vJGY6LLWnGlA&s',
                'link': 'https://www.imdb.com/title/tt1180583/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Munbe Vaa - Sillunu Oru Kaadhal",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b273ee67ff5664c9991b2bd2894e',
                'link': 'https://open.spotify.com/track/6vZj02bcQqLTYRAi4jRkw7',
                'language': 'tamil'
            },
            {
                'title': "Nenjukkul Peidhidum - Vaaranam Aayiram",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b273812bfb4e32feb448e527e8b1',
                'link': 'https://open.spotify.com/track/4vlMdXsRpAIXYggwbNHZSv',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Kadal Pura - Sujatha',
                'image_url': 'https://a.media-amazon.com/images/I/512AR-I-slL.jpg',
                'link': 'https://www.amazon.in/Kadal-Pura-3-Parts-Sandilyan/dp/B00IDUQ7XS',
                'language': 'tamil'
            }
        ]
    },
    'angry': {
        'movies': [
            {
                'title': 'Pariyerum Perumal',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzD41bP_SfFq4-w3ILSHwaX9w2fzB-ZOstMQ&s',
                'link': 'https://www.imdb.com/title/tt8176054/',
                'language': 'tamil'
            },
            {
                'title': 'Asuran',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQOxOYd2huwXn6hL4QvU53DkXsP6BPqbPRbw&s',
                'link': 'https://www.imdb.com/title/tt9477520/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Kutty Story - Master",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b273ab041b1a5273cfa910e22cbe',
                'link': 'https://open.spotify.com/track/0Xm3PXjA4kXu2GxBhkLk61',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Vel Paari - Sujatha',
                'image_url': 'Vel Paari - Sujatha',
                'link': 'https://www.amazon.in/Velpari-%E0%AE%B5%E0%AF%80%E0%AE%B0%E0%AE%AF%E0%AF%81%E0%AE%95-%E0%AE%A8%E0%AE%BE%E0%AE%AF%E0%AE%95%E0%AE%A9%E0%AF%8D-%E0%AE%B5%E0%AF%87%E0%AE%B3%E0%AF%8D-%E0%AE%AA%E0%AE%BE%E0%AE%B0%E0%AE%BF/dp/938810417X',
                'language': 'tamil'
            }
        ]
    },
    'disgust': {
        'movies': [
            {
                'title': 'Ratsasan',
                'image_url': 'https://m.media-amazon.com/images/M/MV5BMjgzMzMxMzUtNzUyYi00NTkxLWI1NTAtMjZhNmMxMGQ4YjBmXkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                'link': 'https://www.imdb.com/title/tt7060344/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Rakita Rakita - Jagame Thandhiram",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b27347ad22841c86a2d90fc345e7',
                'link': 'https://open.spotify.com/track/2oNRoniEFnPdaCfkOQ9m0C',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Yavana Rani - Sandilyan',
                'image_url': 'https://a.media-amazon.com/images/I/61GusJTV8yL.SY445_SX342.jpg',
                'link': 'https://www.amazon.in/Yavana-Rani-2-Parts-Sandilyan/dp/B00IDUQ59Y',
                'language': 'tamil'
            }
        ]
    },
    'fear': {
        'movies': [
            {
                'title': 'Pizza',
                'image_url': 'https://m.media-amazon.com/images/M/MV5BNjVjYTEwYmQtMDM1YS00YTQ3LWI4NzMtMGVlNzFhMTJiZGI3XkEyXkFqcGc@.V1.jpg',
                'link': 'https://www.imdb.com/title/tt2585562/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Aarambikkum Podhu - Pizza",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b27308136f08ec5b2badd58aa304',
                'link': 'https://open.spotify.com/track/1f1KByLdhqe0kr0AgUSBp4',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Sivagamiyin Sabadham - Kalki Krishnamurthy',
                'image_url': 'https://a.media-amazon.com/images/I/517EbhYRWFL.SY445_SX342.jpg',
                'link': 'https://www.amazon.in/Sivagamiyin-Sabatham-Kalki-R-Krishnamurthy/dp/1983588555',
                'language': 'tamil'
            }
        ]
    },
    'neutral': {
        'movies': [
            {
                'title': '96',
                'image_url': 'https://m.media-amazon.com/images/M/MV5BMGI5M2Q4MDktOWVlOS00MzVjLWJlNzktMWZmYTkwOGI2MDc4XkEyXkFqcGc@.V1.jpg',
                'link': 'https://www.imdb.com/title/tt7019842/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Life of Pazham - Thiruchitrambalam",
                'image_url': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.imdb.com%2Ftitle%2Ftt11772746%2F&psig=AOvVaw2Mdh_JMa2YbUKmyEX5gSPs&ust=1746347762651000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCODijL3yho0DFQAAAAAdAAAAABAE',
                'link': 'https://open.spotify.com/album/5jZCyxy9WjBt4EjVaX6akb',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Alai Osai - Kalki Krishnamurthy',
                'image_url': 'https://a.media-amazon.com/images/I/61C0XwmXyoL.SL1360.jpg',
                'link': 'https://www.amazon.in/Alai-Osai-Kalki-R-Krishnamurthy/dp/1975792378',
                'language': 'tamil'
            }
        ]
    },
    'surprise': {
        'movies': [
            {
                'title': 'Super Deluxe',
                'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAgkMjZ64qzRbJLW8cDYGb18qmRax9w1kC-g&s',
                'link': 'https://www.imdb.com/title/tt7019942/',
                'language': 'tamil'
            }
        ],
        'music': [
            {
                'title': "Kannazhaga - The Kiss of Love",
                'image_url': 'https://i.scdn.co/image/ab67616d0000b2730d66934f5370419636c78f18',
                'link': 'https://open.spotify.com/track/2MwCoo4GeXpi8soWn9EiPo',
                'language': 'tamil'
            }
        ],
        'books': [
            {
                'title': 'Parthiban Kanavu - Kalki Krishnamurthy',
                'image_url': 'https://a.media-amazon.com/images/I/516HLpW5QrL.SY445_SX342.jpg',
                'link': 'https://www.amazon.in/Parthiban-Kanavu-Kalki/dp/8184934912',
                'language': 'tamil'
            }
        ]
    }
},

    'malayalam': {
        'happy': {
            'movies': [
                {
                    'title': 'Bangalore Days',
                    'image_url': 'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcT8imdwzY7rRMGXd7zfNBacpee0YmPB471cPOnWKfLnw12wJx6zzn-Al4j-A3OlfVS12nESqg',
                    'link': 'https://www.imdb.com/title/tt3668162/',
                    'language': 'malayalam'
                },
                {
                    'title': 'Premam',
                    'image_url': 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcRtDk2nDidlUBpsu6Ih6GiM2tNlKTb3bqqNXuAEBvJDKT8s--0gDnaantskLYi5WnITHFSb',
                    'link': 'https://www.imdb.com/title/tt4679210/',
                    'language': 'malayalam'
                },
                {
                    'title': 'Ustad Hotel',
                    'image_url': 'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQbqla7QhnDOvHMhDKsZ3bfY2uOWne4cejjQP8xxyMrOFO7FnCxYBVXt3a6qjzbkVPsq6yi9w',
                    'link': 'https://www.imdb.com/title/tt2218988/',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Aaromale - Vinnaithaandi Varuvaayaa",
                    'image_url': 'https://i.ytimg.com/vi/q7OUFE3dw6E/maxresdefault.jpg',
                    'link': 'https://open.spotify.com/track/5Toj8uGqy5Tyb6nXxPU3RD',
                    'language': 'malayalam'
                },
                {
                    'title': "Malare - Premam",
                    'image_url': 'https://i.ytimg.com/vi/0G2VxhV_gXM/maxresdefault.jpg',
                    'link': 'https://open.spotify.com/track/5HyRZXe8kLlkljjSjKv8iL',
                    'language': 'malayalam'
                },
                {
                    'title': "Thumbi Thullal - Cold Case",
                    'image_url': 'https://i.ytimg.com/vi/Dj6DPX53Vfk/maxresdefault.jpg',
                    'link': 'https://open.spotify.com/album/5y44O8p8DJC9dcZTBlIsoV',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Aadujeevitham - Benyamin',
                    'image_url': 'https://m.media-amazon.com/images/I/51yycIHL8LL.UF1000,1000_QL80.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.amazon.in%2FAatujeevitham-Malayalam-Benyamin-ebook%2Fdp%2FB01N598L8P&psig=AOvVaw1DkwcYbPNL9Xr8NuT8eT9R&ust=1746342829034000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCKCG0Yzgho0DFQAAAAAdAAAAABAI',
                    'language': 'malayalam'
                },
                {
                    'title': 'Randamoozham - M.T. Vasudevan Nair',
                    'image_url': 'https://m.media-amazon.com/images/I/51uYhICCgxL.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.amazon.in%2FRandamoozham-M-T-Vasudevan-Nair%2Fdp%2F8122611885&psig=AOvVaw1EPJoX9e3_VnNhMQZPkZus&ust=1746342890490000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCIiGyqvgho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ]
        },
        'sad': {
            'movies': [
                {
                    'title': 'Thanmatra',
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/74/Thanmatra_film1.jpg',
                    'link': 'https://www.imdb.com/title/tt0483180/?ref_=nv_sr_srsg_0_tt_4_nm_4_in_0_q_Thanmatra',
                    'language': 'malayalam'
                },
                {
                    'title': 'Kireedam',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BMjNmM2IxZDQtZWI1OS00MGZiLTgxN2QtOThiYWFkNDg5N2Y5XkEyXkFqcGc@.V1.jpg',
                    'link': 'https://www.imdb.com/title/tt0237376/?ref_=fn_all_ttl_1',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Ennile Ellina - Thanmatra",
                    'image_url': 'https://i.ytimg.com/vi/dp60S_29PyY/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLBA1dLwAYS0DpftAwa_EHSB1zwDXw',
                    'link': 'https://open.spotify.com/track/4X54tVzCd1BQkcMBNY4xOd',
                    'language': 'malayalam'
                },
                {
                    'title': "Manasa Maine - Ustad Hotel",
                    'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT5t3utFkE-x4nZ84Vh3sHwPxyDu1Q8y6zKDw&s',
                    'link': 'https://www.youtube.com/watch?v=BXmpftgvuvY',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Mayyazhippuzhayude Theerangalil - M. Mukundan',
                    'image_url': 'https://m.media-amazon.com/images/I/91ofVlsNZZL.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.amazon.in%2FMayyazhippuzhayute-Theerangalil-M-Mukundan%2Fdp%2F8171302319&psig=AOvVaw2ThlwPfyEJkPbO8ywzGBgj&ust=1746342040973000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCPDwiZXdho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ]
        },
        'angry': {
            'movies': [
                {
                    'title': 'Drishyam',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BM2MwMjNlNjctYjA2ZS00ZDA4LWJmNTYtODg5NDY1YzQzZDg2XkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.imdb.com%2Ftitle%2Ftt3417422%2F&psig=AOvVaw0kyWCeioXZ-WiKTFk202qt&ust=1746341508678000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCLCJ-Zbbho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                },
                {
                    'title': 'Ee.Ma.Yau',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNDQ0NTI1NjMtZTUyZC00YzljLWE4N2QtNzFhNjY0MTY2NWU0XkEyXkFqcGc@.V1.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.imdb.com%2Ftitle%2Ftt7231194%2F&psig=AOvVaw0TVqTLdY2V48A1wrDbecep&ust=1746341560548000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCMCo_7Xbho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Oru Naal Varum - Drishyam",
                    'image_url': 'https://i.ytimg.com/vi/NBnKm2hOH58/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLCaXwihEBbkj3yxXsH51_EVHIqXGQ',
                    'link': 'https://open.spotify.com/album/3UuuOEy72UcavXCYxJd6t9',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Khasakkinte Ithihasam - O.V. Vijayan',
                    'image_url': 'https://m.media-amazon.com/images/I/81vqxexnWBL.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.amazon.in%2FKhasakkinte-Ithihasam-VIJAYAN-V%2Fdp%2FB007E4WHU6&psig=AOvVaw3OUtRh6TAJxprwvRkbd22r&ust=1746341709078000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCNj2xvbbho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ]
        },
        'disgust': {
            'movies': [
                {
                    'title': 'Bhoothakalam',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BZjNmZmZmYzAtMWI2Mi00ZTdmLWE4ZTUtMzNkYmFiMzhkYjVjXkEyXkFqcGc@.V1.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.imdb.com%2Ftitle%2Ftt15560626%2F&psig=AOvVaw3aqXlgt-CstwdB91-eW71Z&ust=1746343042979000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCLjxxvLgho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Aarariro - Bhoothakalam",
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b2739abc7a13ea0580d0f7645e55',
                    'link': 'https://open.spotify.com/track/6Nrcc2kaZ5j0ZjLWNkh7YC',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Daivathinte Vikrithikal - M. Mukundan',
                    'image_url': 'https://m.media-amazon.com/images/I/2112j8t26BL.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://m.media-amazon.com/images/I/2112j8t26BL.AC_UF1000,1000_QL80.jpg',
                    'language': 'malayalam'
                }
            ]
        },
        'fear': {
            'movies': [
                {
                    'title': 'Manichitrathazhu',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BNjllNGZiYjAtMjVjMy00ZGI4LThiZDAtYzFlOGRkY2E0NDA3XkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.imdb.com%2Ftitle%2Ftt0214915%2F&psig=AOvVaw1BZk7KBK0YvvSlXFxX3ECo&ust=1746343107473000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCICJ-5Phho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Poomkaattil - Manichitrathazhu",
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b27308197f202715e645e2cf2a4a',
                    'link': 'https://open.spotify.com/album/4aqSDwVZYIJMdfYzfKlpez',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Yakshi - Malayattoor Ramakrishnan',
                    'image_url': '  https://m.media-amazon.com/images/I/61iXYqKiZ1L.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.amazon.in%2FYAKSHI-MALAYATTOOR-RAMAKRISHNAN%2Fdp%2F8171305008&psig=AOvVaw2Z33feX1zZhzGtBgiuflZ8&ust=1746342942898000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCMiXkcPgho0DFQAAAAAdAAAAABAE',
                    'language': 'malayalam'
                }
            ]
        },
        'neutral': {
            'movies': [
                {
                    'title': 'Maheshinte Prathikaaram', 
                    'image_url': 'https://i.ytimg.com/vi/OzAnJCsUGWw/hqdefault.jpg',
                    'link': 'https://open.spotify.com/search/Maheshinte%20Prathikaaram%20song',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Ayalathe Pennu - Maheshinte Prathikaaram", 
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/3/33/Maheshinte_Prathikaaram.jpg/250px-Maheshinte_Prathikaaram.jpg',
                    'link': 'https://open.spotify.com/track/4DA0K49lY1vvhGmMt8Vdrn',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Naalukettu - M.T. Vasudevan Nair', 
                    'image_url': 'https://m.media-amazon.com/images/I/61tBpjaaxjL.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://www.amazon.in/Naalukettu-M-T-Vasudhevan-nair/dp/812261387X',
                    'language': 'malayalam'
                }
            ]
        },
        'surprise': {
            'movies': [
                {
                    'title': 'Joji', 
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/4/44/Joji_2021.jpg',
                    'link': 'https://www.imdb.com/title/tt13206926/?ref_=fn_all_ttl_1',
                    'language': 'malayalam'
                }
            ],
            'music': [
                {
                    'title': "Thaaram - Joji", 
                    'image_url': 'https://i.ytimg.com/vi/ImhK01DJroQ/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLDLxXOATwAOLNGGO4u8GsRLnR64Vw',
                    'link': 'https://open.spotify.com/artist/29t7mv5S6lSSOlVhPAFP2y',
                    'language': 'malayalam'
                }
            ],
            'books': [
                {
                    'title': 'Oru Desathinte Katha - S.K. Pottekkatt', 
                    'image_url': 'https://a.media-amazon.com/images/I/91PSYUr9uFL._SL1500_.jpg',
                    'link': 'https://www.amazon.in/ORU-DESATHINTE-KATHA-POTTEKKAT-S/dp/8171305709',
                    'language': 'malayalam'
                }
            ]
        }
    },
    'kannada': {
        'happy': {
            'movies': [
                {
                    'title': 'Mungaru Male', 
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/4/47/MM-02.jpg',
                    'link': 'http://www.imdb.com/title/tt0986329/',
                    'language': 'kannada'
                },
                {
                    'title': 'Kirik Party',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BODIxNTFjYTYtODdjYi00ZWI5LWI5MjItZmZkMjJhNjA2MjhhXkEyXkFqcGc@.V1.jpg',
                    'link': 'http://www.imdb.com/title/tt6054758/',
                    'language': 'kannada'
                },
                {
                    'title': 'Gaalipata',
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/4/4a/Galipata.jpg',
                    'link': 'http://www.imdb.com/title/tt1773441/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'Anisutide Yaako Indee - Mungaru Male', 
                    'image_url': 'https://i.ytimg.com/vi/V9pjwUsDq4U/sddefault.jpg',
                    'link': 'https://open.spotify.com/track/4yFxuEx4YwpGpFQ7EaXT4o',
                    'language': 'kannada'
                },
                {
                    'title': 'Bombe Helutaithe - Kirik Party',
                    'image_url': 'https://c.saavncdn.com/126/Kirik-Party-Kannada-2016-500x500.jpg',
                    'link': 'https://open.spotify.com/track/3UuKZajdrLoYCwqlSFy0PE',
                    'language': 'kannada'
                },
                {
                    'title': 'Malegalalli Madumagalu - Gaalipata',
                    'image_url': 'https://m.media-amazon.com/images/I/41bIgiH9l0L.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://open.spotify.com/album/13vJBrp7IY5ZMOIshQTjEO',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Mookajjiya Kanasugalu - K. Shivaram Karanth', 
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/52/MookajjiyaKanasugaluCover.jpg',
                    'link': 'https://www.amazon.in/Mukajjiya-Kanasugalu-Gnyaanapeeta-Prashasthi-Puraskrutha/dp/817285062X',
                    'language': 'kannada'
                },
                {
                    'title': 'Chidambara Rahasya - K. Shivaram Karanth',
                    'image_url': 'https://m.media-amazon.com/images/I/31uzLUzMPsL.AC_UF1000,1000_QL80.jpg',
                    'link': 'https://www.amazon.in/Chidambara-Rahasya-Kp-Poornachandra-Thejasvi/dp/B092RS6BH2',
                    'language': 'kannada'
                }
            ]
        },
        'sad': {
            'movies': [
                {
                    'title': 'Milana', 
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/d3/Milanaposter.jpg',
                    'link': 'http://www.imdb.com/title/tt1881010/',
                    'language': 'kannada'
                },
                {
                    'title': 'Mungaru Male 2',
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BYTA4OWE5OTAtMWU2OC00NDM4LTlmYjUtZjYzMGFkOGExNDc4XkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                    'link': 'http://www.imdb.com/title/tt5762190/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'Nee Sanihake Bandare - Milana', 
                    'image_url': 'https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/2d/df/d6/2ddfd6b0-3958-a125-60e4-1f603b37aeca/cover.jpg/1200x1200bb.jpg',
                    'link': 'https://open.spotify.com/track/0b6KZkeFlKAMZnYKEJdfLD',
                    'language': 'kannada'
                },
                {
                    'title': 'Kanasalu Neene - Mungaru Male 2',
                    'image_url': 'https://i.ytimg.com/vi/1FdRPPmS1M8/maxresdefault.jpg',
                    'link': 'https://open.spotify.com/track/4SFQUIqwAREFnxJAnEKSoG',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Karvalo - Kuvempu', 
                    'image_url': 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1307465538i/5298977.jpg',
                    'link': 'http://www.amazon.in/dp/B073QLMPH3',
                    'language': 'kannada'
                }
            ]
        },
        'angry': {
            'movies': [
                {
                    'title': 'KGF: Chapter 1', 
                    'image_url': 'https://m.media-amazon.com/images/S/pv-target-images/8349bd9a0847617dc0a21182e6897a22a5f67b3bac3c7d9521a0c5f2fdd0c716.jpg',
                    'link': 'http://www.imdb.com/title/tt3320542/',
                    'language': 'kannada'
                },
                {
                    'title': 'Ugramm',
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/77/Ugramm.jpg',
                    'link': 'https://www.imdb.com/title/tt3569782/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'Salaam Rocky Bhai - KGF: Chapter 1', 
                    'image_url': 'https://i.scdn.co/image/ab67616d0000b273994aa4a9e3d5f9e834db97d7',
                    'link': 'https://open.spotify.com/track/1e04JEvKIj6LmrmQaeVohx',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Mankuthimmana Kagga - D.V. Gundappa', 
                    'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/10/MankuthimmanaKaggaCover.jpg',
                    'link': 'http://www.amazon.in/dp/8192395502',
                    'language': 'kannada'
                }
            ]
        },
        'disgust': {
            'movies': [
                {
                    'title': 'RangiTaranga', 
                    'image_url': 'https://static.toiimg.com/thumb/msid-47414700,imgsize-102146,width-400,resizemode-4/47414700.jpg',
                    'link': 'http://www.imdb.com/title/tt4432480/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'RangiTaranga Theme - RangiTaranga', 
                    'image_url': 'https://static.toiimg.com/thumb/msid-47414700,imgsize-102146,width-400,resizemode-4/47414700.jpg',
                    'link': 'https://open.spotify.com/track/6H8QGhkgdQ8T2J0X0X1q0L',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Ghachar Ghochar - Vivek Shanbhag', 
                    'image_url': 'https://m.media-amazon.com/images/I/61LAZyZABPL.jpg',
                    'link': 'http://www.amazon.in/dp/9351776174',
                    'language': 'kannada'
                }
            ]
        },
        'fear': {
            'movies': [
                {
                    'title': 'Lucia', 
                    'image_url': 'https://images.ottplay.com/images/bhajarangi-2-803.jpeg',
                    'link': 'http://www.imdb.com/title/tt2358592/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'Nee Sigoovaregu - Lucia', 
                    'image_url': 'https://images.ottplay.com/images/bhajarangi-2-803.jpeg',
                    'link': 'https://open.spotify.com/track/1t1jHcQAYhXQXlemfGQTSA',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Mysuru Mallige - K.S. Narasimhaswamy', 
                    'image_url': 'https://cdn01.sapnaonline.com/product_media/5551234103899/md_5551234103899.jpg',
                    'link': 'http://www.amazon.in/dp/B083KKLWD1'
                }
            ]
        },
        'neutral': {
            'movies': [
                {
                    'title': 'Godhi Banna Sadharana Mykattu', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BOGEwYmQyYTItZjAzMC00MjFjLWJkZmMtZTA4NDFjNGZmYjQ5XkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                    'link': 'http://www.imdb.com/title/tt4909506/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'Ondu Malebillu - Godhi Banna Sadharana Mykattu', 
                    'image_url': 'https://m.media-amazon.com/images/M/MV5BOGEwYmQyYTItZjAzMC00MjFjLWJkZmMtZTA4NDFjNGZmYjQ5XkEyXkFqcGc@.V1_FMjpg_UX1000.jpg',
                    'link': 'https://open.spotify.com/track/7zalI0bZ7TUF6UWg18tRd7',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Malgudi Days - R.K. Narayan', 
                    'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRo_lFFC1DoVBT07eeO3_PtE7WS32g3sFfVXQ&s',
                    'link': 'http://www.amazon.in/dp/8185986177',
                    'language': 'kannada'
                }
            ]
        },
        'surprise': {
            'movies': [
                {
                    'title': 'Ulidavaru Kandanthe', 
                    'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSf6lPzQ-SErWXZ1AxhnvuFKcN6FTl6kDuBjQ&s',
                    'link': 'http://www.imdb.com/title/tt3394420/',
                    'language': 'kannada'
                }
            ],
            'music': [
                {
                    'title': 'Kanna Muchche - Ulidavaru Kandanthe', 
                    'image_url': 'https://c.saavncdn.com/419/Ulidavaru-Kandanthe-Kannada-2014-500x500.jpg',
                    'link': 'https://open.spotify.com/track/0nLjzPJpdM3KnHyxXp4yHh',
                    'language': 'kannada'
                }
            ],
            'books': [
                {
                    'title': 'Samskara - U.R. Ananthamurthy', 
                    'image_url': 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1347419412i/1057231.jpg',
                    'link': 'http://www.amazon.in/dp/8175812761',
                    'language': 'kannada'
                }
            ]
        }
    }
}
def preprocess_face(face):
    face_resized = cv2.resize(face, (48, 48))
    face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
    face_normalized = face_gray / 255.0
    face_input = np.expand_dims(face_normalized, axis=0)
    face_input = np.expand_dims(face_input, axis=-1)
    return face_input

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            return render_template('signup.html', error='All fields are required')
        
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        
        if not User.validate_password(password):
            return render_template('signup.html', error='Password must be at least 8 characters')
        
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error='Username already exists')
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['logged_in'] = True
            return redirect(url_for('language_selection'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/language_selection')
def language_selection():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('language_selection.html')

@app.route('/set_languages', methods=['POST'])
def set_languages():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    selected_languages = request.form.getlist('languages')
    
    if not selected_languages:
        return render_template('language_selection.html', error='Please select at least one language')
    
    session['selected_languages'] = selected_languages
    
    if session.get('user_id'):
        user = User.query.get(session['user_id'])
        if user:
            user.set_languages(selected_languages)
            db.session.commit()
    
    return redirect(url_for('camera'))

@app.route('/skip_login', methods=['POST'])
def skip_login():
    session['logged_in'] = True
    session['username'] = 'guest'
    session['selected_languages'] = ['english']
    return redirect(url_for('camera'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/camera')
def camera():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('camera.html')

@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    try:
        if 'image' not in request.files:
            return {'error': 'No image provided'}, 400
        
        file = request.files['image']
        nparr = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return {'error': 'No face detected'}, 400
        
        x, y, w, h = faces[0]
        face_region = frame[y:y+h, x:x+w]
        face_input = preprocess_face(face_region)
        
        predictions = emotion_model.predict(face_input)
        predicted_label_index = np.argmax(predictions)
        emotion = emotion_labels[predicted_label_index]
        confidence = float(predictions[0][predicted_label_index])
        
        session['emotion'] = emotion
        session['confidence'] = confidence
        
        return {
            'emotion': emotion,
            'confidence': confidence,
            'all_predictions': predictions[0].tolist()
        }
        
    except Exception as e:
        print(f"Detection error: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/recommendations')
def recommendations():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    emotion = session.get('emotion', 'happy').lower()
    selected_languages = session.get('selected_languages', ['english'])
    
    recommendations = {
        'movies': [],
        'music': [],
        'books': []
    }
    
    for lang in selected_languages:
        if lang in RECOMMENDATIONS and emotion in RECOMMENDATIONS[lang]:
            lang_rec = RECOMMENDATIONS[lang][emotion]
            for category in ['movies', 'music', 'books']:
                if category in lang_rec:
                    recommendations[category].extend(lang_rec[category])
    
    # Fallback to English happy if no recommendations found
    if not any(recommendations.values()):
        lang_rec = RECOMMENDATIONS['english']['happy']
        for category in ['movies', 'music', 'books']:
            if category in lang_rec:
                recommendations[category].extend(lang_rec[category])
    
    return render_template('recommendations.html',
                         emotion=emotion,
                         recommendations=recommendations)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')
            admin.preferred_languages = 'english,hindi'
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)