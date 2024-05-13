from openai import OpenAI

from database import sql
import re


def op_post_names_generator(db, board_name, open_ai_api_client):
    prompt = f"""Generate thread names on 4chan 
    in {db.get_board_info(board_name)[0]["short_description"]}:"""

    generated_data = open_ai_api_client.chat.completions.create(messages=[
        {
            "role": "system",
            "content": ""
        },
        {
            "role": "user",
            "content": prompt
        }],
        model=db.get_setting_value("model"),
        temperature=float(db.get_setting_value("temperature")),
        max_tokens=int(db.get_setting_value("max_tokens"))
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


def op_post_generator(db, open_ai_api_client, op_post_name):
    prompt = f"""Generate OP-post on 4chan on theme: {op_post_name}"""

    generated_data = open_ai_api_client.chat.completions.create(messages=[
        {
            "role": "system",
            "content": ""
        },
        {
            "role": "user",
            "content": prompt
        }],
        model=db.get_setting_value("model"),
        temperature=float(db.get_setting_value("temperature")),
        max_tokens=int(db.get_setting_value("max_tokens_for_op_post"))
    )
    print(generated_data.choices[0].message.content)

    return generated_data.choices[0].message.content


if __name__ == '__main__':
    db = sql()

    open_ai_api_client = OpenAI(base_url=db.get_setting_value("openai_base_url"),
                                api_key=db.get_setting_value("openai_api_key"))

    temperature = float(db.get_setting_value("temperature"))
    max_tokens = int(db.get_setting_value("max_tokens"))

    op_post_names = op_post_names_generator(db, "b", open_ai_api_client)
    print(op_post_names)

    for op_post_name in op_post_names:
        op_post_generator(db, open_ai_api_client, op_post_name)
        print("\n")
