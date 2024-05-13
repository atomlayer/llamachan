import sqlite3
import time
import re
import traceback
from datetime import datetime


class sql:

    def __init__(self):
        self.db_file = 'db.db'

    def db_create(self):
        connection = sqlite3.connect(self.db_file)
        cursor = connection.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    comment TEXT,
                                    subject TEXT,
                                    thread_id INTEGER,
                                    number_in_thread INTEGER,
                                    date_time_of_creation TIMESTAMP, 
                                    image_file_name TEXT
                                ); ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS threads (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject TEXT, 
                            board_name TEXT,
                            last_update_time INTEGER,  
                            is_your_thread INTEGER
                        );''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS boards (
                                            name TEXT,
                                            short_description TEXT,
                                            full_description TEXT
                                        ); ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                                            short_description TEXT,
                                            full_description TEXT,
                                            value TEXT,
                                            default_value TEXT, 
                                            permissible_values TEXT,
                                            category TEXT
                                        ); ''')

        connection.commit()
        connection.close()

        self.create_last_update_time_idx()

        self.add_new_board('b', '/b - random')
        self.add_new_board('a', '/a - anime')
        self.add_new_board('pol', '/pol - politics')

        self.add_setting(short_desc="openai_base_url", value="http://localhost:11434/v1/", category="llm api")
        self.add_setting(short_desc="openai_api_key", value="llamachan", category="llm api")
        self.add_setting(short_desc="temperature", value="0.7", category="llm api")
        self.add_setting(short_desc="model", value="command-r:latest", category="llm api")
        self.add_setting(short_desc="max_tokens", value="4096", category="llm api")

        # self.add_setting(short_desc="automatic1111_host", value="127.0.0.1", category="automatic1111 api")

        self.add_setting(short_desc="automatic1111_host", value="192.168.50.154", category="automatic1111 api")

        self.add_setting(short_desc="automatic1111_port", value="7860", category="automatic1111 api")
        self.add_setting(short_desc="automatic1111_use_https", value="0", category="automatic1111 api")
        self.add_setting(short_desc="automatic1111_sampler", value="Euler a", category="automatic1111 api")
        self.add_setting(short_desc="automatic1111_steps", value="20", category="automatic1111 api")
        self.add_setting(short_desc="automatic1111_negative_prompt", value="ugly, out of frame",
                         category="automatic1111 api")
        self.add_setting(short_desc="automatic1111_cfg_scale", value="7", category="automatic1111 api")

        self.add_setting(short_desc="max_tokens_for_op_post", value="300")
        self.add_setting(short_desc="max_tokens_for_thread", value="4096")
        self.add_setting(short_desc="max_tokens_for_image_prompt", value="150")
        self.add_setting(short_desc="number_of_threads_on_the_page", value="10")
        self.add_setting(short_desc="probability_of_a_picture_appearing_in_a_post", value="20")

    def create_last_update_time_idx(self):
        connection = sqlite3.connect(self.db_file)
        cursor = connection.cursor()

        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='index' AND name='last_update_time_idx';
        ''')

        if cursor.fetchone() is None:
            cursor.execute('''
                CREATE UNIQUE INDEX last_update_time_idx ON threads(last_update_time);
            ''')

        connection.commit()
        connection.close()

    def _execute_query(self, sql, islog=False):
        conn = sqlite3.connect(self.db_file)

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()

            if islog:
                print("Query executed successfully")
        except sqlite3.Error as e:
            print(f"Error executing SQL query: {e}")
            traceback.print_exc()
        finally:
            conn.close()

    def _select_json(self, sql, islog=False):
        conn = sqlite3.connect(self.db_file)
        result = None

        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            description = [x[0] for x in cursor.description]
            output = []
            for n in result:
                output.append(dict(zip(description, n)))
            result = output

            if islog:
                print(result)
        except sqlite3.Error as e:
            print(f"Error executing SQL query: {e}")
            traceback.print_exc()
        finally:
            conn.close()

        return result

    def get_board_info(self, board_name: str):
        return self._select_json(f"""select * from boards where name = '{board_name}'""")

    def create_thread(self, subject: str, board_name: str, is_your_thread: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        current_time = int(time.time())  # Get the current Unix timestamp
        cursor.execute(
            "INSERT INTO threads (subject, board_name, last_update_time, is_your_thread) VALUES (?, ?, ?, ?)", (
                subject, board_name, current_time, is_your_thread))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

    def set_last_update_time_for_thread(self, thread_id):
        current_time = int(time.time())  # Get the current Unix timestamp
        self._execute_query(f"update threads set last_update_time = {current_time} where id = {thread_id}")

    def get_thread_data(self, thread_id):
        return self._select_json(f"""select * from threads where id = {thread_id}""")

    def add_post(self, comment, subject, thread_id, number_in_thread, image_file_name):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO posts (comment, subject, thread_id, number_in_thread,
                          date_time_of_creation, image_file_name) VALUES (?, ?, ?, ?, ?, ?)''',
                       (comment, subject, thread_id, number_in_thread, datetime.now(), image_file_name))
        conn.commit()
        conn.close()
        self.set_last_update_time_for_thread(thread_id)

    def add_setting(self, short_desc, value, default_value=None, permissible_values=None,
                    full_desc=None, category=None):

        if self.get_setting(short_desc) is None:
            if default_value is None:
                default_value = value

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            sql = '''INSERT OR IGNORE INTO settings(short_description, full_description, 
                                        value, default_value, permissible_values, category) 
                     VALUES (?, ?, ?, ?, ?, ?)'''

            cursor.execute(sql, (short_desc, full_desc, value, default_value, permissible_values, category))
            cursor.connection.commit()
            conn.close()

    def change_setting(self, short_desc, new_value):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        sql = '''UPDATE settings SET value = ? WHERE short_description = ?'''
        cursor.execute(sql, (new_value, short_desc))
        cursor.connection.commit()
        conn.close()

    def get_setting(self, short_desc):
        res = self._select_json(f"""SELECT * FROM settings WHERE short_description = '{short_desc}'""")
        if len(res) > 0:
            return res[0]

    def get_setting_value(self, short_desc):
        return self.get_setting(short_desc)["value"]

    def add_inside_links(self, post):
        # regex_patterns = [r'[Nn][Oo]\.', r'[aA]nonymous\s[Nn][Oo]\.']
        # new_text = post
        # for pattern in regex_patterns:
        #     new_text = re.sub(pattern, ">>", new_text)

        def replace_no_with_link(match):
            number = match.group(1)
            return f'<a class="post_link" href="#no_{number}">>{number}</a>'

        # Заменяем "no.X" на ссылки в формате <a class="post_link" href="#no_X">#X</a>
        new_text = re.sub(r'[Nn][Oo]\.(\d+)', replace_no_with_link, post)

        return new_text

    def modify_posts(self, posts):
        for i, n in enumerate(posts):
            if posts[i]["comment"].startswith("OP: "):
                posts[i]["comment"] = posts[i]["comment"][3:]
                posts[i]["subject"] = "OP"
            if posts[i]["comment"].startswith("OP Anonymous: "):
                posts[i]["comment"] = posts[i]["comment"][14:]
                posts[i]["subject"] = "OP"
            if posts[i]["comment"].startswith(": "):
                posts[i]["comment"] = posts[i]["comment"][2:]

            # posts[i]["comment"] = self.add_inside_links(posts[i]["comment"])

        return posts

    def get_posts_by_thread_id(self, thread_id):
        posts = self._select_json(f"""
                select id as post_id, comment, subject, number_in_thread, 
                date_time_of_creation, image_file_name from posts
                where thread_id = {thread_id}
                order by number_in_thread""")
        return self.modify_posts(posts)

    def get_last_post_number_in_thread(self, thread_id):
        return int(self._select_json(f"""
                 select MAX(number_in_thread) as max from posts
                 where thread_id = {thread_id}""")[0]["max"])

    def get_last_posts_by_thread_id(self, thread_id, number_in_thread):
        posts = self._select_json(f"""
                select id as post_id, comment, subject, number_in_thread, 
                date_time_of_creation, image_file_name from posts
                where thread_id = {thread_id} and number_in_thread > {number_in_thread}
                order by number_in_thread""")
        return self.modify_posts(posts)

    def get_count_of_threads_on_board(self, board_name):
        res = self._select_json(f"""select count(*) as thread_count from threads where board_name = '{board_name}'""")
        return res[0]['thread_count']

    def get_board_threads_data(self, board_name, page_number):
        number_of_threads_on_the_page = int(self.get_setting_value("number_of_threads_on_the_page"))

        threads = self._select_json(f"""select * from threads where board_name = '{board_name}' 
                                order by last_update_time desc 
                                limit {page_number * number_of_threads_on_the_page}, {number_of_threads_on_the_page}""")

        for i, n in enumerate(threads):
            threads[i]["posts"] = self.get_posts_by_thread_id(n["id"])
        return threads

    def get_board_names(self):
        return self._select_json("select name from boards")

    def get_all_boards(self):
        return self._select_json("select * from boards")

    def get_all_settings(self):
        return self._select_json("select * from settings")

    def update_all_settings(self, data):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        for n in data:
            sql = '''UPDATE settings SET value = ? WHERE short_description = ?'''
            cursor.execute(sql, (n[1], n[0]))

        cursor.connection.commit()
        conn.close()

    def add_new_board(self, name, short_description, full_description=None):
        res = self._select_json(f"""select * from boards where name='{name}'""")
        if len(res) == 0:

            if full_description is None:
                full_description = short_description
            self._execute_query(f"""INSERT INTO boards (name, short_description, full_description)
                                    values ('{name}', '{short_description}', '{full_description}') """)

    def add_image_to_op_post(self, thread_id, img_file_name):
        self._execute_query(f""" update posts 
                                 set image_file_name = '{img_file_name}'
                                 where thread_id = {thread_id}
                                 and number_in_thread = 1""")
