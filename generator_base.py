import abc


class GeneratorBase(abc.ABC):

    @abc.abstractmethod
    def initialize(self):
        pass

    @abc.abstractmethod
    def generate_op_post_topics(self, board_name):
        pass

    @abc.abstractmethod
    def generate_op_post(self, op_post_topic, board_name):
        pass

    @abc.abstractmethod
    def generate_new_posts(self, posts):
        pass

    @abc.abstractmethod
    def generate_image_prompt(self, message):
        pass