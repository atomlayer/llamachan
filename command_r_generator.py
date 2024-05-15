from openai import OpenAI
from generator_base import GeneratorBase
import re


class CommandRGenerator(GeneratorBase):

    def __init__(self, db):
        self.db = db
        self.initialize()

    def initialize(self):
        self.open_ai_api_client = OpenAI(base_url=self.db.get_setting_value("openai_base_url"),
                                         api_key=self.db.get_setting_value("openai_api_key"))

    def generate_op_post_topics(self, board_name):
        prompt = f"""Generate thread names on 4chan 
        in {self.db.get_board_info(board_name)[0]["short_description"]}:"""

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": ""
            },
            {
                "role": "user",
                "content": prompt
            }],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=int(self.db.get_setting_value("max_tokens"))
        )
        print(generated_data)

        generated_data = generated_data.choices[0].message.content
        generated_data = generated_data.split("\n")

        output = []
        for n in generated_data:
            if re.match(r"^\d+", n):
                temp = re.sub(r"^\d+\. ", "", n)
                temp = re.sub(r"^\d+ ", "", temp)
                temp = temp.strip()
                output.append(temp)

        if len(output) == 0:
            for n in generated_data:
                temp = n.strip()
                output.append(temp)

        return output[:10]

    def generate_op_post(self, op_post_topic):
        prompt = f"""Generate OP-post on 4chan on theme: {op_post_topic}"""

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": ""
            },
            {
                "role": "user",
                "content": prompt
            }],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=int(self.db.get_setting_value("max_tokens_for_op_post"))
        )
        print(generated_data.choices[0].message.content)

        return generated_data.choices[0].message.content

    def _find_posts(self, text):
        regex = r"([Aa]nonymous(\s|.+?)[Nn]o\.\d+)|([Aa]nonymous.+?\\n)"
        matches = re.findall(regex, text, flags=re.MULTILINE)

        if not matches:
            return [text]

        def split(txt, seps):
            default_sep = seps[0]
            for sep in seps[1:]:
                txt = txt.replace(sep, default_sep)
            return [i.strip() for i in txt.split(default_sep)]

        split_result = split(text, [n[0] for n in matches])
        split_result = [x for x in split_result if x != "" and x != "OP"]

        return split_result

    def generate_new_posts(self, posts):

        max_tokens = int(self.db.get_setting_value("max_tokens_for_thread"))
        system_prompt = "Continue the dialog on 4chan. You can add links to other posts " \
                        "(example no.1 - link to the post). Don't answer for OP."

        prompt = []
        for i, n in enumerate(posts):
            if i == 0:
                prompt.append("OP Anonymous no.1\n")
            else:
                prompt.append(f"Anonymous no.{i + 1}\n")
            prompt.append(n)
            prompt.append("\n")

        prompt = "".join(prompt)

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=max_tokens
        )
        print(generated_data)

        generated_data = generated_data.choices[0].message.content
        posts = self._find_posts(generated_data)

        return posts

    def generate_image_prompt(self, message):
        prompt = f"""Message: {message}  


        Message subject:"""

        generated_data = self.open_ai_api_client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": ""
            },
            {
                "role": "user",
                "content": prompt
            }],
            model=self.db.get_setting_value("model"),
            temperature=float(self.db.get_setting_value("temperature")),
            max_tokens=int(self.db.get_setting_value("max_tokens_for_image_prompt"))
        )
        print(generated_data.choices[0].message.content[:150])

        return generated_data.choices[0].message.content[:150]
