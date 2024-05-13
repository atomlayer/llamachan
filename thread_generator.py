from openai import OpenAI
import re


def find_posts(text):
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


def llm_generate(thread_data, db):
    client = OpenAI(base_url=db.get_setting_value("openai_base_url"),
                    api_key=db.get_setting_value("openai_api_key"))

    max_tokens = int(db.get_setting_value("max_tokens_for_thread"))
    system_prompt = "Continue the dialog on 4chan. You can add links to other posts (example no.1 - link to the post)"

    prompt = []
    for i, n in enumerate(thread_data):
        if i == 0:
            prompt.append("OP Anonymous no.1\n")
        else:
            prompt.append(f"Anonymous no.{i + 1}\n")
        prompt.append(n)
        prompt.append("\n")

    prompt = "".join(prompt)

    generated_data = client.chat.completions.create(messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }],
        model=db.get_setting_value("model"),
        temperature=float(db.get_setting_value("temperature")),
        max_tokens=max_tokens
    )
    print(generated_data)

    generated_data = generated_data.choices[0].message.content
    posts = find_posts(generated_data)

    return posts
