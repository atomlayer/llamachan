from flask import render_template
import threading
from flask import Flask, request, jsonify
from openai import OpenAI
import os

from automatic1111_api_client import ImageGenerator
from database import sql
import uuid
from flask import redirect, url_for
from op_post_generator import op_post_names_generator, op_post_generator
from thread_generator import llm_generate
import random

app = Flask(__name__)
db = sql()
db.db_create()
img_generator = ImageGenerator(db)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

amount_of_new_posts_in_new_thread = 5

open_ai_api_client = OpenAI(base_url=db.get_setting_value("openai_base_url"),
                            api_key=db.get_setting_value("openai_api_key"))
probability_of_a_picture_appearing_in_a_post = int(db.get_setting_value("probability_of_a_picture_appearing_in_a_post"))


def create_thread(comment, subject, board_name, image_file_name, is_your_thread):
    thread_id = db.create_thread(subject, board_name, is_your_thread)
    db.add_post(comment, subject, thread_id, 1, image_file_name)
    return thread_id


def generate_new_posts(thread_id, amount_of_new_posts=5):
    posts = [x['comment'] for x in db.get_posts_by_thread_id(thread_id)]
    last_post_number = len(posts)

    new_post_count = 0



    while new_post_count < amount_of_new_posts:
        new_posts = llm_generate(posts, db)
        posts.extend(new_posts)

        for n in new_posts:
            last_post_number += 1
            new_post_count += 1

            new_image_file_name=""
            random_number = random.randint(0, 100)
            if random_number <= probability_of_a_picture_appearing_in_a_post:
                image_prompt = img_generator.generate_prompt(message=n)
                new_image_file_name = str(uuid.uuid4()) + ".png"
                img_generator.generate_image(prompt=image_prompt, file_name=new_image_file_name)


            db.add_post(n, "", thread_id, last_post_number, new_image_file_name)


@app.route('/get_more_posts', methods=['POST'])
def get_more_posts():
    data = request.get_json()
    threading.Thread(target=generate_new_posts, args=(data['thread_id'],)).start()
    return "", 200


@app.route('/thread/<thread_id>', methods=['GET'])
def open_thread(thread_id):
    if thread_id.isdigit():
        thread_data = db.get_thread_data(int(thread_id))
        if len(thread_data) == 0:
            return "Thread doesn't exist"
        thread_data = thread_data[0]

        data = {}
        data['thread_id'] = thread_id
        data['thread_subject'] = thread_data["subject"]
        data['board_name'] = thread_data["board_name"]

        posts = db.get_posts_by_thread_id(thread_id)
        data["op"] = posts[0]

        if len(posts[1:]) == 0:
            threading.Thread(target=generate_new_posts, args=(thread_id,)).start()

        board_names = db.get_board_names()
        data["board_names"] = board_names
        data["board_name_count"] = len(board_names)

        return render_template('thread.html', data=data)
    else:
        return "Thread doesn't exist"


def upload_image(image_file):
    file_extension = image_file.filename.split(".")[-1]
    new_image_file_name = str(uuid.uuid4()) + "." + file_extension
    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_image_file_name))
    return new_image_file_name


@app.route('/create_new_thread', methods=['POST'])
def create_new_thread():
    subject = request.form.get('subject')
    comment = request.form.get('comment')

    if subject == "":
        subject = comment[:70]

    board_name = request.form.get('board_name')
    image_file = request.files.get('image_file')
    new_image_file_name = upload_image(image_file)

    thread_id = create_thread(comment, subject, board_name, new_image_file_name, is_your_thread=1)

    return redirect(url_for('open_thread', thread_id=thread_id))


@app.route('/', methods=['GET'])
def get_index():
    boards = db.get_all_boards()
    data = {}
    data["boards"] = boards
    return render_template('index.html', data=data)


@app.route('/get_post_list', methods=['POST'])
def get_post_list():
    data = request.json

    thread_id = data["thread_id"]
    last_post_number = int(data["last_post_number"])
    last_posts = db.get_last_posts_by_thread_id(thread_id, last_post_number)

    return jsonify(last_posts), 200


@app.route('/add_post', methods=['POST'])
def add_post():
    data = request.form
    thread_id = data["thread_id"]
    comment = "OP: " + data["comment"]

    new_image_file_name = ""
    if request.files.get('image_file').filename != "":
        image_file = request.files.get('image_file')
        new_image_file_name = upload_image(image_file)

    last_post_number = db.get_last_post_number_in_thread(thread_id)
    db.add_post(comment, "", thread_id, last_post_number + 1, new_image_file_name)

    threading.Thread(target=generate_new_posts, args=(thread_id,)).start()

    return "", 200


def generate_image_for_op_post(thread_id, prompt):
    img_file_name = str(uuid.uuid4()) + ".png"
    img_generator.generate_image(file_name=img_file_name, prompt=prompt)
    db.add_image_to_op_post(thread_id, img_file_name)


def generate_new_threads(board_name):
    op_post_names = op_post_names_generator(db, board_name, open_ai_api_client)
    op_post_names = op_post_names[:3]

    for op_post_name in op_post_names:
        op_post = op_post_generator(db, open_ai_api_client, op_post_name)
        thread_id = create_thread(op_post, op_post_name[:150], board_name, None, is_your_thread=False)

        generate_new_posts(thread_id, amount_of_new_posts=3)

        generate_image_for_op_post(thread_id, op_post_name[:150])


@app.route('/generate_more_threads', methods=['POST'])
def generate_more_threads():
    data = request.get_json()
    generate_new_threads(data["board_name"])
    return "", 200


@app.route('/<board>', methods=['GET'])
@app.route('/<board>/<number>', methods=['GET'])
def handle_board(board, number=None):
    board_info = db.get_board_info(board)

    if len(board_info) > 0:
        board_info = board_info[0]
        data = {"board": board_info["name"],
                "board_title": board_info["short_description"]}

        count_of_threads = db.get_count_of_threads_on_board(board_info["name"])
        if count_of_threads < 2:
            generate_new_threads(board_info["name"])

        if number is None:
            number = 0

        data["pages"] = [_ for _ in
                         range(int(count_of_threads / int(db.get_setting_value("number_of_threads_on_the_page"))))]

        data["threads"] = db.get_board_threads_data(board_info["name"], int(number))

        board_names = db.get_board_names()
        data["board_names"] = board_names
        data["board_name_count"] = len(board_names)

        return render_template('board.html', data=data)
    else:
        return "Invalid board"


@app.route('/settings', methods=['GET'])
def view_settings():
    settings = db.get_all_settings()

    data = {}
    data["settings"] = settings
    board_names = db.get_board_names()
    data["board_names"] = board_names
    data["board_name_count"] = len(board_names)

    return render_template('settings.html', data=data)


@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.form
    data = data.items()
    db.update_all_settings(data)

    data = {}
    data["settings"] = db.get_all_settings()

    board_names = db.get_board_names()
    data["board_names"] = board_names
    data["board_name_count"] = len(board_names)

    return render_template('settings.html', data=data)


@app.route('/add_board', methods=['GET'])
def add_board():
    data = {}
    board_names = db.get_board_names()
    data["board_names"] = board_names
    data["board_name_count"] = len(board_names)

    return render_template('add_board.html', data=data)


@app.route('/add_new_board', methods=['POST'])
def add_new_board():
    data = request.form
    db.add_new_board(data["board_name"], data["board_description"])
    return "", 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5623)
    # app.run(host="0.0.0.0", port=5623)
