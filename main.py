import webbrowser
from flask import render_template
import threading
from flask import Flask, request, jsonify
import os
from automatic1111_api_client import ImageGenerator
from database import sql
import uuid
from flask import redirect, url_for
from llama3_generator import Llama3Generator

app = Flask(__name__)
db = sql()
db.db_create()
img_generator = ImageGenerator(db)
llm_generator = Llama3Generator(db)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

amount_of_new_posts_in_new_thread = 5

uploads_folder_path = os.path.join("static", "uploads")
if not os.path.exists(uploads_folder_path):
    os.makedirs(uploads_folder_path)


def create_thread(comment, subject, board_name, image_file_name, is_your_thread):
    thread_id = db.create_thread(subject, board_name, is_your_thread)

    is_OP = False
    if is_your_thread == 1:
        is_OP = True

    db.add_post(comment=comment,
                subject=subject,
                thread_id=thread_id,
                number_in_thread=1,
                image_file_name=image_file_name,
                text_description_of_the_attached_picture="",
                is_OP=is_OP)
    return thread_id


def generate_new_posts(thread_id, amount_of_new_posts=5):
    posts = [x for x in db.get_posts_by_thread_id(thread_id)]
    # last_post_number = len(posts)

    new_post_count = 0
    board_info = db.get_board_info_by_thread_id(thread_id)

    while new_post_count < amount_of_new_posts:
        new_posts = llm_generator.generate_new_posts(posts=posts, board_name=board_info["name"])

        for i, n in enumerate(new_posts):
            new_posts[i]["number_in_thread"] = n["id"]
            new_posts[i]["is_OP"] = 1 if new_posts[i]["is_OP"] else 0
            new_posts[i]["comment"] = n["text"]
            if n.get("text_description_of_the_attached_picture") is None:
                new_posts[i]["text_description_of_the_attached_picture"] = ""


        posts.extend(new_posts)

        for n in new_posts:
            # last_post_number += 1
            new_post_count += 1

            new_image_file_name = ""

            if n.get('text_description_of_the_attached_picture') and n["text_description_of_the_attached_picture"] != "":
                if db.is_an_API_used_to_generate_images():
                    new_image_file_name = str(uuid.uuid4()) + ".png"
                    img_generator.generate_image(prompt=n["image_description"], file_name=new_image_file_name)

            db.add_post(comment=n["comment"],
                        subject="",
                        thread_id=thread_id,
                        number_in_thread=n["number_in_thread"],
                        image_file_name=new_image_file_name,
                        text_description_of_the_attached_picture=n["text_description_of_the_attached_picture"],
                        is_OP=n["is_OP"])


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
    db.add_post(comment=comment,
                subject="",
                thread_id=thread_id,
                number_in_thread=last_post_number + 1,
                image_file_name=new_image_file_name,
                text_description_of_the_attached_picture="",
                is_OP=True)

    threading.Thread(target=generate_new_posts, args=(thread_id,)).start()

    return "", 200


def generate_image_for_op_post(thread_id, prompt):
    img_file_name = str(uuid.uuid4()) + ".png"
    img_generator.generate_image(file_name=img_file_name, prompt=prompt)
    db.add_image_to_op_post(thread_id, img_file_name)


def generate_new_threads(board_info):
    op_post_topics = llm_generator.generate_op_post_topics(board_info['short_description'])
    op_post_topics = op_post_topics[:3]

    for op_post_topic in op_post_topics:
        op_post = llm_generator.generate_op_post(op_post_topic=op_post_topic,
                                                 board_short_description=board_info['short_description'])
        thread_id = create_thread(op_post, op_post_topic[:150], board_info['name'], "", is_your_thread=False)

        generate_new_posts(thread_id, amount_of_new_posts=3)

        if db.is_an_API_used_to_generate_images():
            generate_image_for_op_post(thread_id, op_post_topic[:150])


@app.route('/generate_more_threads', methods=['POST'])
def generate_more_threads():
    data = request.get_json()
    board_info = db.get_board_info(data["board_name"])
    generate_new_threads(board_info)
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
            generate_new_threads(board_info)

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

    img_generator.initialize()
    llm_generator.initialize()

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
    webbrowser.open('http://localhost:5623')
    app.run(debug=False, host="0.0.0.0", port=5623)
