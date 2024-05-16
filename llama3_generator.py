import dirtyjson
from openai import OpenAI
import re
import json5
# import tolerantjson as tjson
# from fix_busted_json import repair_json
import json_repair


from database import sql


class Llama3Generator:

    def __init__(self, db):
        self.db = db
        self.initialize()

    def initialize(self):
        self.open_ai_api_client = OpenAI(base_url=self.db.get_setting_value("openai_base_url"),
                                         api_key=self.db.get_setting_value("openai_api_key"))


    def try_eval(self, json_data):
        try:
            json_data = eval(json_data)
            return json_data
        except:
            return None


    def try_dirtyjson_lib_parser(self, json_data, is_list=False, is_dict=False):
        try:
            json_data = dirtyjson.loads(json_data)

            if is_list:
                return list(json_data)
            if is_dict:
                return dict(json_data)
            return json_data
        except:
            return None

    def try_json5_lib_parser(self, json_data):
        try:
            json_data = json5.loads(json_data)
            return json_data
        except:
            return None

    def extract_json_array(self, text):
        json_pattern = r'\[([^]]*)\]'
        match = re.search(json_pattern, text)

        if match:
            json_data_txt = '[' + match.group(1) + ']'
            json_data_txt =json_repair.repair_json(json_data_txt)

            json_data =self.try_eval(json_data_txt)
            if json_data is None:
                json_data = self.try_dirtyjson_lib_parser(json_data_txt, is_list=True)
            if json_data is None:
                json_data = self.try_json5_lib_parser(json_data_txt)

            return json_data

    def extract_json_dict(self, text):
        json_pattern = r'{([^}]*)}'
        match = re.search(json_pattern, text)

        if match:
            json_data_str = match.group(1)
            json_data_str =json_data_str.strip()
            json_data_txt = '{' + json_data_str + '}'
            json_data_txt = json_repair.repair_json(json_data_txt)

            json_data =self.try_eval(json_data_txt)
            if json_data is None:
                json_data = self.try_dirtyjson_lib_parser(json_data_txt, is_dict=True)
            if json_data is None:
                json_data = self.try_json5_lib_parser(json_data_txt)

            return json_data

    def generate_op_post_topics(self, board_short_description):

        schema = [
            {'theme': 'op post theme'}
        ]

        prompt = f"""Generate thread topics for section '{board_short_description}' on 4chan. Output in valid JSON using the schema defined here: {schema}."""

        print(prompt)

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {"role": "system", "content": ""},
            {"role": "user", "content": prompt}],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=int(self.db.get_setting_value("max_tokens"))
        )
        print(generated_data.choices[0].message.content)

        themes_list = self.extract_json_array(generated_data.choices[0].message.content)
        output = [n["theme"] for n in themes_list]
        return output

    def generate_op_post(self, op_post_topic, board_short_description):

        schema = {'text': 'op post text'}

        prompt = f"""Generate an op-post on 4chan on the topic {op_post_topic} on the {board_short_description} board. Output in valid JSON using the schema defined here: {schema}."""

        print(prompt)

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {"role": "system", "content": ""},
            {"role": "user", "content": prompt}],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=int(self.db.get_setting_value("max_tokens"))
        )
        print(generated_data.choices[0].message.content)

        generated_data = generated_data.choices[0].message.content
        generated_data = generated_data.replace("\n\n", "<br>")
        output = self.extract_json_dict(generated_data)
        output = output["text"]
        return output

    def generate_new_posts(self, posts, board_name):

        board_short_description = self.db.get_board_info(board_name)[0]["short_description"]

        posts_prompt = []

        # try:

        for post in posts:
            post_data = {
                    "id": post["number_in_thread"],
                    "is_OP": True if post["is_OP"] == 1 else False,
                    "name": "Anonymous",
                    "text": post["comment"],
                    "text_description_of_the_attached_picture": post["text_description_of_the_attached_picture"]
            }
            posts_prompt.append(post_data)
        # except:
        #     pass

        posts_prompt_dict = {"posts": posts_prompt}

        prompt = f"""Continue the dialogue on 4chan on the {board_short_description} board. You can add links to other posts (example >>1 - link to the post). Don't answer for OP. You can give a text description of the picture for your posts. Output only new records in valid JSON format  
  
{posts_prompt_dict}"""

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {"role": "system", "content": ""},
            {"role": "user", "content": prompt}],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=int(self.db.get_setting_value("max_tokens_for_thread"))
        )
        generated_data = generated_data.choices[0].message.content
        generated_data.replace("\\n\\n", "<br>").replace("\n", "").replace("\\", "")
        print(generated_data)
        new_posts = self.extract_json_dict(generated_data)
        new_posts = new_posts["posts"]
        current_max_number = max([n["number_in_thread"] for n in posts])

        output = []
        for n in new_posts:
            n = dict(n)
            if n["id"] > current_max_number:
                output.append(n)

        return output


if __name__ == '__main__':
    db = sql()
    #
    generator = Llama3Generator(db)

    output = generator.extract_json_dict("""```json
{
  'text': 'You ever notice how fatty foods just hit different? That greasy mouthfeel and indulgent flavor is like nothing else. Why does food high in fat taste so fucking good? Is it some evolved preference for the energy-dense goodness or what?
'
}
```""")

    print(output)


