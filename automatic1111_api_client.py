import os.path
import webuiapi
from openai import OpenAI


class ImageGenerator:

    def __init__(self, db):
        self.db = db
        self.initialize()

    def initialize(self):
        if self.db.is_an_API_used_to_generate_images():
            use_https = True if self.db.get_setting_value("automatic1111_use_https") == "1" else False
            self.api = webuiapi.WebUIApi(host=self.db.get_setting_value("automatic1111_host"),
                                         port=int(self.db.get_setting_value("automatic1111_port")),
                                         use_https=use_https,
                                         sampler=self.db.get_setting_value("automatic1111_sampler"),
                                         steps=self.db.get_setting_value("automatic1111_steps"))
            self.llm_client = OpenAI(base_url=self.db.get_setting_value("openai_base_url"),
                                     api_key=self.db.get_setting_value("openai_api_key"))

    def generate_image(self, prompt, file_name):
        result = self.api.txt2img(prompt=prompt,
                                  negative_prompt=self.db.get_setting_value("automatic1111_negative_prompt"),
                                  seed=-1,
                                  styles=[],
                                  cfg_scale=int(self.db.get_setting_value("automatic1111_cfg_scale")),
                                  #                      sampler_index='DDIM',
                                  #                      steps=30,
                                  #                      enable_hr=True,
                                  #                      hr_scale=2,
                                  #                      hr_upscaler=webuiapi.HiResUpscaler.Latent,
                                  #                      hr_second_pass_steps=20,
                                  #                      hr_resize_x=1536,
                                  #                      hr_resize_y=1024,
                                  #                      denoising_strength=0.4,

                                  )
        # images contains the returned images (PIL images)
        image = result.images[0]  # Assuming you want to save the first image in the list

        image.save(os.path.join("static", "uploads", file_name))
