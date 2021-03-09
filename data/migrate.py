import datetime

from users import User
from posts import Post
import sqlite3
import json
import os

users = dict()

if os.path.isfile(os.path.abspath('./users/users.json')):
    users = json.load(open(os.path.abspath('./users/users.json')), cls=User.UserDecoder)
if os.path.isfile(os.path.abspath('./posts/posts.json')):
    posts = json.load(open(os.path.abspath('./posts/posts.json')), cls=Post.PostDecoder)

db = sqlite3.connect('karma.db')
cur = db.cursor()

for user in users.values():
    cur.execute(f'INSERT INTO users (user_id, post_karma, link_karma) VALUES({user.user_id},{user.post_karma},{user.link_karma})')
for post in posts.values():
    contentfixed = post.content.replace('"', '')
    authorfixed = post.author.replace('"', '')
    cur.execute(f'INSERT INTO posts (message_url, message_id, upvotes, downvotes, content, author, created_at) VALUES("{post.message_url}", {post.message_id}, {post.upvotes}, {post.downvotes}, "{contentfixed}", "{authorfixed}", "{post.created_at.strftime("%Y-%m-%d %H:%M:%S")}")')

db.commit()
cur.close()
db.close()
